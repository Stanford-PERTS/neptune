// Relies on some data being mocked by the presurvey component, since it's too
// difficult to mock all the different surveys and pd on the server side.
// Mocked behavior is trigged by the "trout viper" and "trout cobra" codes.
// See the presurvey component for details.

var qualtricsDomain = 'https://sshs.qualtrics.com';

describe("presurvey new participant, open cohort, complete survey", function () {
  var participantName = 'new-open-complete';

  beforeEach(function () {
    // The portal is tested separately, so just use a link that combines
    // everything together, including arbitrary query string parameters that
    // might come from ISRs. We'll test that they are appended when we arrive
    // at the survey.
    //browser.get('/participate/portal/trout-viper/1/puffin?foo=bar&baz=qux');
    // Change of plan. We're not supporting the query string bit, so don't
    // test for it.
    browser.get('/participate/portal/trout-viper/1/' + participantName);
  });

  it("should redirect to Qualtrics", function () {
    // The presence of query string parameters could be tested by appending
    // more stuff on the urlContains() argument, as long as we trust the
    // ordering.
    browser.wait(protractor.ExpectedConditions.urlContains(qualtricsDomain), 5000);
  });

  // This is an old copy of the previous test, preserved in the comments
  // in case I need to know how to run code when an off-site url is loaded.
  // it("should redirect to Qualtrics", function () {
  //   // http://stackoverflow.com/questions/28808463/what-is-browser-ignoresynchronization-in-protractor
  //   browser.ignoreSynchronization = true;
  //   browser.wait(protractor.ExpectedConditions.urlContains('qualtrics.com'), 5000);
  //   // http://stackoverflow.com/questions/29397800/how-can-i-get-the-current-url-using-protractor
  //   browser.getCurrentUrl().then(function(url) {
  //     // Grab and process the query string.
  //     // @todo(chris): use URI.js instead
  //     var queryStringIndex = url.indexOf('?') || url.length;
  //     var queryString = url.slice(queryStringIndex);
  //     var queryParams = queryStringToObject(queryString);

  //     // ...we should be at Qualtrics!
  //     expect(getDomain(url)).toEqual(qualtricsDomain);

  //     // ...with data in the query string!
  //     //expect(queryParams.foo).toEqual('bar');
  //     //expect(queryParams.baz).toEqual('qux');
  //     // ...except not, see comments in beforeEach()

  //     // Cleanup so later tests have the default value of false
  //     browser.ignoreSynchronization = false;
  //     return url;
  //   });

  //   // Cleanup so later tests have the default value of false
  //   browser.ignoreSynchronization = false;
  // });

});

describe("presurvey new participant, open cohort, ready survey", function () {
  var participantName = 'new-open-ready';

  beforeEach(function () {
    browser.get('/participate/portal/trout-viper/2/' + participantName);
  });

  it("should redirect to Qualtrics", function () {
    browser.wait(protractor.ExpectedConditions.urlContains(qualtricsDomain), 5000);
  });
});

describe("presurvey new participant, open cohort, not ready survey", function () {
  var participantName = 'new-open-unready';

  beforeEach(function () {
    browser.get('/participate/portal/trout-viper/3/' + participantName);
  });

  it("should end at an error message", function () {
    expect(element(by.id('error-message')).isDisplayed()).toBe(true);
  });
});
