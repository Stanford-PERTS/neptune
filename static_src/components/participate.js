import presurveyEpAssent from './presurveyEpAssent';
import presurveyEpBlockSwitcher from './presurveyEpBlockSwitcher';

const registerComponents = ngModule => {
  // Example of a component-as-decorator, see ./helloWorld.js.
  // helloWorld(ngModule);
  presurveyEpAssent(ngModule);
  presurveyEpBlockSwitcher(ngModule);
};

export default registerComponents;
