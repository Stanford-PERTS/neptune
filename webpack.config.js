/* global module, process, require, __dirname */

const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const appName = process.env.APP === 'participate' ? 'participate' : 'neptune';

if (process.env.NODE_ENV === 'development') {
  // DEVELOPMENT MODE
  // Both neptune and participate apps are always run/built.
  module.exports = {
    // Enable development mode
    // https://webpack.js.org/concepts/mode/
    mode: 'development',

    devServer: {
      // Required for ui-router / html5mode.
      // https://webpack.js.org/configuration/dev-server/#devserver-historyapifallback
      // https://developer.mozilla.org/en-US/docs/Web/API/History
      historyApiFallback: {
        rewrites: [
          // Handles /participate/* routes.
          { from: /^\/participate/, to: '/participate' },
          // Handles all other routes.
          { from: /./, to: '/' },
        ],
      },
      // Send any requests matching these patterns to the back end server,
      // i.e. the app engine sdk. Makes managing links and domains vastly
      // simpler in client code; no CORS!
      // https://webpack.js.org/configuration/dev-server/#devserver-proxy
      proxy: [{
        context: [
          // Defined in app.yaml
          '/api',
          '/cron',
          '/datasets',
          '/map',
          '/static',
          '/task',
          // Defined in view_handlers.py
          '/logout',
          '/admin_login',
          '/facilitator_instructions',
          '/student_handout',
          '/custom_portal_technical_guide',
          '/datasets',
        ],
        target: 'http://localhost:8080',
        // Rewrite the request so the server is none the wiser. This matters
        // when the sdk tries to use various mocked services, like GCS, because
        // it looks for them on the same port as the request (e.g. 8888) but
        // fails b/c the sdk isn't listening on that port.
        // https://github.com/chimurai/http-proxy-middleware#http-proxy-options
        autoRewrite: true,
        changeOrigin: true,
      }],
      // Other apps inside docker containers may sent requests with the host
      // 'host.docker.internal' or something other than 'localhost'.
      disableHostCheck: true,
    },

    // Enable source maps
    // https://webpack.js.org/configuration/devtool/
    devtool: 'cheap-module-source-map',

    // Source JavaScript
    context: `${__dirname}/static_src`,
    entry: {
      neptune: './neptune.js',
      participate: './participate.js',
    },

    // Allow relative paths when importing modules.
    //   import getFullYear from 'utils/getFullYear';
    //   vs import getFullYear from '../../utils.getFullYear';
    //
    // https://webpack.js.org/configuration/resolve/#resolve-modules
    resolve: {
      modules: [
        // First, look in `node_modules`
        'node_modules',
        // Then, look in `static_src`
        `${__dirname}/static_src`,
      ],
    },

    // Destination JavaScript
    output: {
      path: `${__dirname}/static`,
      // In-memory only, no file is generated during development.
      filename: 'static/[name].js',
    },

    plugins: [
      // Inject CSS/JS includes into the HTML file
      // https://github.com/jantimon/html-webpack-plugin
      new HtmlWebpackPlugin({
        chunks: ['neptune'],
        inject: true,
        template: 'neptune.html', // relative to context
        filename: `${__dirname}/static/index.html`,
        cache: false,
      }),
      new HtmlWebpackPlugin({
        chunks: ['participate'],
        inject: true,
        template: 'participate.html', // relative to context
        filename: `${__dirname}/static/participate/index.html`,
        cache: false,
      }),
    ],

    module: {
      // Webpack loader config rules
      // https://webpack.js.org/concepts/loaders/
      rules: [
        {
          test: /\.js$/,
          use: [
            // Babel Loader, so we can it through babel and utilize .babelrc
            // https://github.com/babel/babel-loader
            'babel-loader',
          ],
        },
        {
          test: /\.scss$/,
          use: [
            // Adds CSS to the DOM by injecting a <style> tag
            // https://github.com/webpack-contrib/style-loader
            'style-loader',
            // Handles imports of CSS
            // https://github.com/webpack-contrib/css-loader
            'css-loader',
            // Transforms CSS styles, for vendor prefixes
            // https://github.com/postcss/postcss-loader
            // https://github.com/postcss/postcss
            'postcss-loader',
            // Compiles Sass to CSS
            // https://github.com/webpack-contrib/sass-loader
            'sass-loader',
          ],
        },
        {
          test: /\.(jpe?g|png|gif|svg)$/i,
          use: [
            // Emits the imported object as file and returns public URL
            // https://webpack.js.org/loaders/file-loader/
            {
              loader: 'file-loader',
              options: {
                // We are outputting to a flat directory so images need to have
                // unique filenames across the app.
                name: `assets/img/[name].[ext]`,
              },
            },
          ],
        },
        {
          test: /\.(html)$/,
          use: {
            loader: 'html-loader',
          },
        },
      ],
    },
  };
} else {
  // PRODUCTION MODE
  // Neptune and participate apps are set up to build separately. Overall build
  // time is similar to building both together. But gives us the flexibility to
  // build only a single app, for quicker build-test cycles.
  module.exports = {
    // Enable production mode
    // https://webpack.js.org/concepts/mode/
    mode: 'production',

    // Enable source maps
    // https://webpack.js.org/configuration/devtool/
    devtool: 'source-map',

    // Source JavaScript
    context: `${__dirname}/static_src`,
    entry: `./${appName}.js`,

    // Allow relative paths when importing modules.
    //   import getFullYear from 'utils/getFullYear';
    //   vs import getFullYear from '../../utils.getFullYear';
    //
    // https://webpack.js.org/configuration/resolve/#resolve-modules
    resolve: {
      modules: [
        // First, look in `node_modules`
        'node_modules',
        // Then, look in `static_src`
        `${__dirname}/static_src`,
      ],
    },

    // Destination JavaScript
    output: {
      path: `${__dirname}/static`,
      publicPath: '/static/',
      filename: `${appName}.[hash].js`,
    },

    optimization: {
      // Group up JavaScript and SCSS files when outputting to files.
      // https://webpack.js.org/plugins/split-chunks-plugin/#optimization-splitchunks
      splitChunks: {
        cacheGroups: {
          js: {
            name: `main`,
            test: /\.js$/,
            chunks: 'all',
            enforce: true,
          },
          styles: {
            name: `main`,
            test: /\.scss$/,
            chunks: 'all',
            enforce: true,
          },
        },
      },
      minimizer: [
        // Uglify JavaScript
        // https://github.com/webpack-contrib/uglifyjs-webpack-plugin
        new UglifyJsPlugin({
          cache: true,
          parallel: true,
          sourceMap: true,
        }),
        // Optimize / Minimize CSS
        // https://github.com/NMFR/optimize-css-assets-webpack-plugin
        new OptimizeCSSAssetsPlugin({}),
        // Inject CSS/JS includes into the HTML file
        // https://github.com/jantimon/html-webpack-plugin
        new HtmlWebpackPlugin({
          inject: true,
          template: `${__dirname}/templates/dist/${appName}.html`,
          // Need to set this because we are storing in a separate directory
          // from all of the other app assets (this defaults to `output.path`).
          filename: `${__dirname}/templates/dist/${appName}.html`,
        }),
      ],
    },

    plugins: [
      // Extract CSS into a file.
      // https://github.com/webpack-contrib/mini-css-extract-plugin
      //
      // This probably won't be needed in Webpack 5 as it looks like extracts
      // will be built into core.
      // https://medium.com/webpack/webpack-4-released-today-6cdb994702d4
      new MiniCssExtractPlugin({
        filename: `${appName}.[hash].css`,
      }),
    ],

    module: {
      // Webpack loader config rules
      // https://webpack.js.org/concepts/loaders/
      rules: [
        {
          test: /\.js$/,
          use: [
            // Babel Loader, so we can it through babel and utilize .babelrc
            // https://github.com/babel/babel-loader
            'babel-loader',
          ],
        },
        {
          test: /\.scss$/,
          use: [
            // Extracts CSS into a file.
            // https://github.com/webpack-contrib/mini-css-extract-plugin
            MiniCssExtractPlugin.loader,
            // Handles imports of CSS
            // https://github.com/webpack-contrib/css-loader
            'css-loader',
            // Transforms CSS styles, for vendor prefixes
            // https://github.com/postcss/postcss-loader
            // https://github.com/postcss/postcss
            'postcss-loader',
            // Compiles Sass to CSS
            // https://github.com/webpack-contrib/sass-loader
            'sass-loader',
          ],
        },
        {
          test: /\.(jpe?g|png|gif|svg)$/i,
          use: [
            // Emits the imported object as file and returns public URL
            // https://webpack.js.org/loaders/file-loader/
            {
              loader: 'file-loader',
              options: {
                // We are outputting to a flat directory so images need to have
                // unique filenames across the app.
                name: `assets/img/[name].[ext]`,
              },
            },
          ],
        },
        {
          test: /\.(html)$/,
          use: {
            loader: 'html-loader',
          },
        },
      ],
    },
  };
}
