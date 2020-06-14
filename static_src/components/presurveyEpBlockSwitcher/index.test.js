// While we don't use this value, the import decorates the `angular` global
// with the participate app and all its components, which we can then inject.
import participateModule from 'participate';

const chooseOne = arr => arr[Math.floor(Math.random() * arr.length)];

const availableMetrics = [
  'feedback-for-growth',
  'meaningful-work',
  'teacher-caring',
];

describe('nepEpBlockSwitcher', () => {
  let $componentController;
  let vm;

  beforeEach(() => {
    // Inject utility for accessing component controller, misc services.
    inject((_$componentController_) => {
      $componentController = _$componentController_;
    });

    // All these tests required the controller and some contextual data.
    vm = $componentController('nepEpBlockSwitcher', null);
  });

  it('should set params for a new user', () => {
    expect(
      vm.applyValidationInterval(undefined)
    ).toEqual(
      {'show_validation': 'true'}
    );
  });

  it('should set params if not validated recently', () => {
    const today = new Date();
    const sixtyOneDays = 61 * 24 * 60 * 60 * 1000;
    expect(
      vm.applyValidationInterval(new Date(today - sixtyOneDays))
    ).toEqual(
      {'show_validation': 'true'}
    );
  });

  it('should NOT set params if HAS validated recently', () => {
    const today = new Date();
    const fortyNineDays = 49 * 24 * 60 * 60 * 1000;
    expect(
      vm.applyValidationInterval(new Date(today - fortyNineDays))
    ).toEqual(
      {}
    );
  });

  it('converts old open response params', () => {
    const trueParams = {
      other_stuff: 'foo',
      // Choose an active lc randomly, to demonstrate that the open response
      // param always matches it, rather than being hard-coded.
      learning_conditions: JSON.stringify(chooseOne(availableMetrics)),
      show_open_response_questions: true,
    };
    expect(
      vm.transformLearningConditionParam(trueParams)
    ).toEqual(
      {
        other_stuff: trueParams.other_stuff,
        learning_conditions: trueParams.learning_conditions,
        open_response_lcs: trueParams.learning_conditions,
      }
    );

    const falseParams = {
      other_stuff: 'foo',
      learning_conditions: JSON.stringify(chooseOne(availableMetrics)),
      show_open_response_questions: false,
    };
    expect(
      vm.transformLearningConditionParam(falseParams)
    ).toEqual(
      {
        other_stuff: 'foo',
        learning_conditions: falseParams.learning_conditions,
        open_response_lcs: '[]',
      }
    );
  });

  it('doesn\'t change new open response params', () => {
    const newParams = {
      other_stuff: 'foo',
      learning_conditions: JSON.stringify(chooseOne(availableMetrics)),
      open_response_lcs: '["meaningful-work"]',
    };
    expect(vm.transformLearningConditionParam(newParams))
      .toEqual(newParams);
  });

  it('chooses only one open response param', () => {
    const params = vm.chooseOneLearningCondition({
      open_response_lcs: JSON.stringify(availableMetrics),
    });
    const lcs = JSON.parse(params.open_response_lcs);
    expect(lcs.length).toEqual(1);
    expect(availableMetrics).toContain(lcs[0]);
  });

});
