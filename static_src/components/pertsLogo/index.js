import pertsLogoImg from './pertslogo.png';

const pertsLogo = ngModule => {
  const template = `
    <img src="${pertsLogoImg}" alt="PERTS" />
  `;

  ngModule.component('pertsLogo', {
    template,
  });
};

export default pertsLogo;
