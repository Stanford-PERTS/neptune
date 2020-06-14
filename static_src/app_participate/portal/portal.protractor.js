var customPortalUrl = 'http://www.example.com/?code=trout-cobra&session=1';
var qualtricsDomain = 'https://sshs.qualtrics.com';

describe("portal first state", function () {

  beforeEach(function () {
    browser.get('/participate');
  });

  it("should display the code input", function () {
    expect(element(by.model('$ctrl.code')).isDisplayed()).toBe(true);
  });

  it("should accept entry of a sessionless code", function () {
    // "trout viper" is populated via /api/everything
    element(by.model('$ctrl.code')).sendKeys('trout viper');
    element(by.id('submitCodeButton')).click();

    // Result is prompting user for the session.
    expect(element(by.model('$ctrl.session')).isDisplayed()).toBe(true);
  });

  it("should accept entry of a code with session", function () {
    // Enter a full code.
    element(by.model('$ctrl.code')).sendKeys('trout viper 1');
    element(by.id('submitCodeButton')).click().then(function () {
      // Protractor seems to magically know that angular is busy with stuff
      // for awhile.
      // Result is prompting user for their token.
      expect(element(by.model('$ctrl.firstName')).isDisplayed()).toBe(true);
      expect(element(by.model('$ctrl.middleInitial')).isDisplayed()).toBe(true);
      expect(element(by.model('$ctrl.lastName')).isDisplayed()).toBe(true);
    });
  });

  it("should reject code if it doesn't exist", function () {
    // Enter a full code.
    element(by.model('$ctrl.code')).sendKeys('nonexistant narwhal');
    element(by.id('submitCodeButton')).click().then(function () {
      // Result is an error message, with the code input still on the screen.
      expect(element(by.binding('$ctrl.codeError')).getText()).toBeTruthy();
      expect(element(by.model('$ctrl.code')).isDisplayed()).toBe(true);
    });
  });

  it("should reject session if it doesn't exist for that program", function () {
    // Enter a full code.
    element(by.model('$ctrl.code')).sendKeys('trout viper 9');
    element(by.id('submitCodeButton')).click().then(function () {
      // Result is an error message, with the code input still on the screen.
      expect(element(by.binding('$ctrl.sessionError')).getText()).toBeTruthy();
      expect(element(by.model('$ctrl.session')).isDisplayed()).toBe(true);
    });
  });
});

describe("custom portal first state", function () {

  beforeEach(function () {
    browser.get('/participate');
  });

  it("should accept entry of a code with session", function () {
    // Enter a full code.
    element(by.model('$ctrl.code')).sendKeys('trout cobra 1');
    // Submit and expect redirection.
    element(by.id('submitCodeButton')).click();

    browser.wait(protractor.ExpectedConditions.urlContains(customPortalUrl), 3000);
  });

});


describe("portal code state", function () {

  beforeEach(function () {
    browser.get(browser.params.localhost + '/participate/portal/trout-viper');
  });

  it("should parse the code in the URL", function () {
    // Value from URL stored in form.
    expect(viewValue('$ctrl.code')).toBe('trout viper');
  });

  it("should display the session input", function () {
    // Response is to prompt user for their session number.
    expect(element(by.model('$ctrl.session')).isDisplayed()).toBe(true);
  });

  it("should accept entry of a session number", function () {
    // Enter a full code.
    element(by.model('$ctrl.session')).sendKeys('1');
    element(by.id('submitSessionButton')).click().then(function () {
      expect(element(by.model('$ctrl.firstName')).isDisplayed()).toBe(true);
      expect(element(by.model('$ctrl.middleInitial')).isDisplayed()).toBe(true);
      expect(element(by.model('$ctrl.lastName')).isDisplayed()).toBe(true);
    });
  });

  it("should reject session if it doesn't exist for that program", function () {
    // Enter a full code.
    element(by.model('$ctrl.session')).sendKeys('9');
    element(by.id('submitSessionButton')).click().then(function () {
      // Result is an error message, with the session input still on the screen.
      expect(element(by.binding('$ctrl.sessionError')).getText()).toBeTruthy();
      expect(element(by.model('$ctrl.session')).isDisplayed()).toBe(true);
    });
  });
});

describe("custom portal code state", function () {

  beforeEach(function () {
    browser.get(browser.params.localhost + '/participate/portal/trout-cobra');
  });

  it("should parse the code in the URL", function () {
    // Value from URL stored in form.
    expect(viewValue('$ctrl.code')).toBe('trout cobra');
  });

  it("should display the session input", function () {
    // Response is to prompt user for their session number.
    expect(element(by.model('$ctrl.session')).isDisplayed()).toBe(true);
  });

  it("should accept entry of a session number", function () {
    // Enter a session number.
    var sessionInput = element(by.model('$ctrl.session'));
    // I don't know why this is required, but it is.
    browser.wait(protractor.ExpectedConditions.visibilityOf(sessionInput), 3000);
    sessionInput.sendKeys('1');
    // Submit and expect redirection
    element(by.id('submitSessionButton')).click();

    browser.wait(protractor.ExpectedConditions.urlContains(customPortalUrl), 3000);
  });

});

describe("portal code state with invalid code", function () {

  beforeEach(function () {
    browser.get('/participate/portal/nonexistant-narwhal');
  });

  it("should reject code in URL if it is invalid", function () {
    // Result is an error message, with the code input still on the screen.
    expect(element(by.binding('$ctrl.codeError')).getText()).toBeTruthy();
    expect(element(by.model('$ctrl.code')).isDisplayed()).toBe(true);
  });

});

describe("portal session state", function () {

  beforeEach(function () {
    browser.get(browser.params.localhost + '/participate/portal/trout-viper/1');
  });

  it("should parse code and session in the URL", function () {
    expect(viewValue('$ctrl.code')).toBe('trout viper');
    expect(viewValue('$ctrl.session')).toBe('1');
  });

  it("should display the name form", function () {
    // Response is to prompt user for their student id.
    expect(element(by.model('$ctrl.firstName')).isDisplayed()).toBe(true);
    expect(element(by.model('$ctrl.middleInitial')).isDisplayed()).toBe(true);
    expect(element(by.model('$ctrl.lastName')).isDisplayed()).toBe(true);
  });

  it("should accept entry for the token", function () {
    element(by.model('$ctrl.firstName')).sendKeys('  Pêrt sy12 ');
    element(by.model('$ctrl.middleInitial')).sendKeys('Ø');
    element(by.model('$ctrl.lastName')).sendKeys('  Persøn æ34 ');
    element(by.id('submitTokenButton')).click().then(function () {
      browser.wait(protractor.ExpectedConditions.urlContains(qualtricsDomain), 5000);
    });
  });

  it("should accept no middle name for the token", function () {
    element(by.model('$ctrl.firstName')).sendKeys('  Pêrt sy12 ');
    element(by.model('$ctrl.noMiddleName')).click();
    element(by.model('$ctrl.lastName')).sendKeys('  Persøn æ34 ');
    element(by.id('submitTokenButton')).click().then(function () {
      browser.wait(protractor.ExpectedConditions.urlContains(qualtricsDomain), 5000);
    });
  });
});

describe("custom portal session state", function () {

  beforeEach(function () {
    browser.get(browser.params.localhost + '/participate/portal/trout-cobra/1');
  });

  it("should redirect", function () {
    browser.wait(protractor.ExpectedConditions.urlContains(customPortalUrl), 3000);
  });
});

describe("portal session state with invalid session", function () {

  beforeEach(function () {
    browser.get('/participate/portal/trout-viper/9');
  });

  it("should reject session in URL if it is invalid", function () {
    // Result is an error message, with the session input still on the screen.
    expect(element(by.binding('$ctrl.sessionError')).getText()).toBeTruthy();
    expect(element(by.model('$ctrl.session')).isDisplayed()).toBe(true);
  });

});

describe("portal token state with new participant, first session", function () {
  beforeEach(function () {
    browser.get(browser.params.localhost + '/participate/portal/trout-viper/1/demo-new');
  });

  // it("should parse code, session, and token in URL", function () {
  //   expect(viewValue('$ctrl.code')).toBe('trout viper');
  //   expect(viewValue('$ctrl.session')).toBe('1');
  //   expect(viewValue('$ctrl.token')).toBe('demo-token');
  // });

  // it("should display the consent screen", function () {
  //   expect(element(by.id('consent')).isDisplayed()).toBe(true);
  //   expect(element(by.model('$ctrl.consent')).isDisplayed()).toBe(true);
  // });
});

describe("portal token state with new participant, non-first session", function () {
  beforeEach(function () {
    browser.get(browser.params.localhost + '/participate/portal/trout-viper/2/demo-skipper');
  });

  // it("should ask skippers if they did session 1", function () {
  //   // Use a special student token that has a mocked history.

  //   expect(element(by.model('$ctrl.didFirstSession')).isDisplayed()).toBe(true);
  // });
});

function viewValue(modelExpression) {
  return element(by.model(modelExpression)).getAttribute('value');
}
