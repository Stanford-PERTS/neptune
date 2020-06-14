## Commands

- Development
    - `npm run server` to start up local App Engine (port 8080)
    - `npm start` to start webpack-dev-server for Neptune/Participate (port 8888)
    - View app at [http://localhost:8888](http://localhost:8888)
- Build
    - `npm build` to build Neptune and Participate
    - `npm run build:neptune` to build only Neptune
    - `npm run build:participate` to build only Participate
- Run Build Locally
    - `npm run build` (or `:neptune` or `:participate`)
    - `npm run server` starts up local App Engine (port 8080)
    - View app at [http://localhost:8080](http://localhost:8080)
- Test
   - `npm test`

## Directory Structure

```
# source directories
static_src/
  neptune.html      << neptune html
  neptune.js        << neptune entry point
  participate.html  << participate html
  participate.js    << participate entry point
  assets/           << static assets, directly copied to `static/`
  components/       << ui components
    neptune.js        << register components function for neptune
    participate.js    << register components function for participate
    button/           << each component is organized into its own directory
      index.js        << component file
      index.test.js   << component test file
      index.scss      << component styles
  ngUtils/          << Angular utility files
    neptune.js        << register utility components for neptune
    participate.js    << register utility components for participate
    *.js              << utilify files
  polyfills         << polyfills
    neptune.js        << register polyfills function for neptune
    participate.js    << register polyfills function for participate
    *.js              << polyfill files, one per function
  routes/           << route files
    neptune.js
    participate.js
  scenes/           << scene components (with app specific logic)
    neptune.js        << register scenes function for neptune
    participate.js    << register scenes function for participate
    home/             << each scene is organized into its own directory
    organizations/    << each scene is organized into its own directory
    ...
  services/         << angular services
    neptune.js        << register services function for neptune
    participate.js    << register services function for participate
    organization/     << each service is organizated into its own directory
    project/          << each service is organizated into its own directory
    ...
  styles/           << style files
    neptune.scss      << neptune's entry style file
    participate.scss  << participate's entry style file
    ...               << other imported files
  utils/            << Plain JavaScript utility functions
    forEachObj.js
    getShortUid.js
    ...

# build directories
static/
  neptune.[hash].css      << neptune css
  neptune.[hash].js       << neptune js
  participate.[hash].css  << participate css
  participate.[hash].js   << participate js
  *                       << static assets, directly copied from `static_src/assets`

templates/
  dist/
    neptune.html      << neptune html
    participate.html  << participate html
```

## NPM

- Always install packages using `--save-exact`.

## Polyfills

To add a polyfill, create a polyfill file named for the function you are polyfilling and import that file in the `static_src/polyfills/index.js` file. Include the source of the polyfill for reference. For example:

```
// static_src/polyfills/Array.prototype.find.js
//
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/find
// https://tc39.github.io/ecma262/#sec-array.prototype.find
if (!Array.prototype.find) {
  Object.defineProperty(Array.prototype, 'find', {
    ...polyfill code here
  })
}

// static_src/polyfills/index.js
//
import './Array.prototype.find.js';
```

Creating a single file per polyfill allows us to easily scan the directory to see which polyfills already exist, edit/remove as needed, or share with another project.

Polyfills can be found at [MDN](https://developer.mozilla.org/en-US/).

Note: `.eslintignore` contains an entry for `static_src` so the polyfills files aren't being linted. This is copy/pasted code in ES5 that doesn't conform to our rules.

## Tech Being Used

### Angular

Front-end JavaScript framework.

### [Angular ui-router](https://ui-router.github.io/ng1/)

UI-Router is the defacto standard for routing in AngularJS.

### [ng-annotate-loader](https://github.com/huston007/ng-annotate-loader)

Automatically annotates Angular dependencies.

### [babel-preset-env](https://github.com/babel/babel-preset-env)

A Babel preset that compiles ES2015+ down to ES5 by automatically determining the Babel plugins and polyfills you need based on your targeted browser or runtime environments.

#### Notes

babel-preset-env uses browserlist, which we have configured in our `package.json` so that the list is shared across plugins (like PostCSS).

#### Resources

- [babel-preset-es2015 -> babel-preset-env](http://babeljs.io/env)
- [babel-preset-env repo](https://github.com/babel/babel-preset-env)

### [sass-loader](https://webpack.js.org/loaders/sass-loader)

The main style file is imported in the entry file for each app.

```
# static_src/neptune.js
import './styles/neptune.scss';

# static_src/participate.js
import './styles/participate.scss';
```

All other style files should be imported from within the SCSS files via the `@import` command. See `static_src/styles/neptune.scss` for an example.

#### Notes

Don't import CSS files. This will break builds. If you want to write plain CSS, write plain CSS and place it into a `.scss` file.

### [mini-css-extract-plugin](https://github.com/webpack-contrib/mini-css-extract-plugin)

Extracts out CSS into its own file.

#### Resources

- https://github.com/webpack-contrib/mini-css-extract-plugin
- https://www.valentinog.com/blog/webpack-4-tutorial/#webpack_4_extracting_CSS_to_a_file
- https://github.com/webpack-contrib/mini-css-extract-plugin#minimizing-for-production

### [html-webpack-plugin](https://github.com/jantimon/html-webpack-plugin)

Injects CSS/JS includes into the HTML.

### [ESLint](https://eslint.org/)

The pluggable linting utility for JavaScript and JSX.

#### Notes

Configuration is very similar to our PERTS/triton repo. I've removed the React extends, React rules and made the following changes to work with our Angular patterns.

To allow for the `const vm = this` assignment we use in our controllers:

```diff
- "babel/no-invalid-this": "warn",
+ "babel/no-invalid-this": "off",
```

```diff
"consistent-this": [
  "warn",
-  "that"
+  "vm"
],
```

#### Resources

- https://eslint.org
- https://github.com/babel/eslint-plugin-babel

### [Prettier](https://github.com/prettier/prettier)

Prettier is an opinionated code formatter.

#### Notes

We're using Prettier in combination with ESLint to help reduce the mental energy involved in making code styling decisions (single quotes or double quotes?). Prettier rules become ESLint rules with the help of `eslint-config-prettier` and `eslint-plugin-prettier`.

#### Resources

- https://prettier.io/
- https://github.com/prettier/prettier
- https://github.com/prettier/eslint-config-prettier
- https://github.com/prettier/eslint-plugin-prettier

### [PostCSS](https://github.com/postcss/autoprefixer)

Adds vendor prefixes and removes outdated prefixes automatically.

#### Notes

The following [browserslist queries](https://github.com/browserslist/browserslist) are being used:

```
"last 2 versions" (of all browsers)
"> 1%" (based on usage stats of all browsers)
```

#### Resources

- https://github.com/postcss/autoprefixer
- https://webpack.js.org/loaders/postcss-loader
- https://github.com/browserslist/browserslist

### [Jest](https://facebook.github.io/jest/index.html)

- running jest for testing (`npm test`)
- need to use preprocessor to filter out scss files (jest.pre.scss.js)
- need to use preprocessor to run test files through babel (babel-jest)
- https://github.com/facebook/jest/tree/master/packages/babel-jest
- https://facebook.github.io/jest/index.html
