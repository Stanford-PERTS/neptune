/**
 * Displays assent text to EP participants and offers the choice to continue or
 * opt out.
 * @param  {Object} ngModule participate module
 * @return {undefined}
 */
const presurveyEpAssent = (ngModule) => {
  function controller() {
    const ASSENT_PD_KEY = 'ep_assent';
    const vm = this;

    vm.doesNotAssent = false;

    vm.$onInit = function () {
      vm.parent.getLoadedData().then((loaded) => {
        const assentPd = loaded.pdArr.find((pd) => pd.key === ASSENT_PD_KEY);
        if (assentPd) {
          // This participant has already responded to our assent prompt,
          // don't show it again.
          vm.parent.nextPresurveyState();
        } else {
          // This participant hasn't seen the assent prompt yet; display it.
          vm.parent.toggleMask();
        }
      });
    };

    vm.continue = function () {
      vm.parent
        .getLoadedData()
        .then((loaded) => {
          const assentPd = vm.parent.createPd(
            loaded,
            ASSENT_PD_KEY,
            vm.doesNotAssent ? 'false' : 'true',
          );
          return assentPd.$save();
        })
        .then(vm.parent.nextPresurveyState);
    };
  }

  ngModule.component('nepEpAssent', {
    controller,
    template: `
      <div class="EpAssent">
        <h1>Help Make School Better For All Students</h1>
        <p>
          Your school is participating in a research study with Stanford
          University. To learn more about the study, read the text below.
        </p>
        <div class="EpAssentConsentText">
          <p>
            <strong>Study Title:</strong> Research to Improve Instructional
            Practices
          </p>

          <p>
            <strong>What will happen in this study?</strong>
          </p>
          <p>
            Your class is about to take a quick survey made by Stanford
            University to help your teacher learn how to make class better for
            you.
          </p>
          <p>
            We are interested in figuring out how your teacher&rsquo;s teaching
            style affects your experience in school. If you agree to be in the
            research study, your school may share academic, disciplinary, or
            attendance records with the Stanford research team. That information
            will be kept <strong>strictly confidential</strong>; it will not be
            shared with anyone outside the research team in a way that could be
            used to figure out who you are. But it will be used, together with
            your survey answers, to help the researchers learn how teachers
            across the country can make school better for students like you.
          </p>
          <p>
            Whether or not you participate in the research, you always may skip
            any survey question without penalty.
          </p>

          <p>
            <strong>Amendments to Terms of Use.</strong> When you first logged
            in, you agreed to the Terms of Use to use this website
            (<a href="https://www.perts.net/terms-of-use" target="_blank">perts.net/terms-of-use</a>).
            The Terms of Use have &ldquo;exculpatory language,&rdquo; which
            means they say that you cannot blame PERTS or Stanford if something
            goes wrong. (PERTS is the group at Stanford University that is doing
            the research.) If you participate in the research, then the
            exculpatory language in the Terms of Use would not apply to you.
            That means, <strong>you would be allowed to hold PERTS and Stanford
            liable (to blame PERTS/Stanford)</strong> if something were to go
            wrong as part of the research.
          </p>
          <p>
            If you say <strong>no</strong> to being in the study, then you will
            still take the survey, but your answers and academic records will
            not be used in the research project to help make school better for
            students like you. In that case, everything in the Terms of Use
            (<a href="https://www.perts.net/terms-of-use" target="_blank">perts.net/terms-of-use</a>)
            applies to you, including Limitation of Liability, Indemnity, Third
            Party Websites, and User Interactions.
          </p>

          <p>
            <strong>Risks or Discomforts of Participating</strong>
          </p>
          <p>
            Nope; everything you&rsquo;ll be doing will be completely safe.
          </p>

          <p>
            <strong>Benefits of Participating</strong>
          </p>
          <p>
            You will help researchers learn more about what students think and
            how they learn. This information will be used to help make school a
            better place for all students to learn.
          </p>

          <p>
            <strong>Who will know I am in the study?</strong>
          </p>
          <p>
            Only the researcher team will know that you&rsquo;re in the study.
            The only people of your school who will know whether or not you
            participate are the people in charge of your academic records,
            including grades, attendance, and disciplinary records.
          </p>

          <p>
            <strong>Who can I talk to about the study?</strong> (Contact
            Information)
          </p>
          <p>
            If you have any questions about the study or any problems to do with
            the study you can contact the Protocol Director, XXXXXXXXXXX. Phone:
            XXXXXXXXXXXXXX; Email: XXXXXXXXXXXXXXXXXXXX.
          </p>
          <p>
            If you have questions about the study and want to talk to someone
            else who is not a part of the study, you can call the Stanford
            Institutional Review Board (IRB) at (650) 723-2480 or toll free at
            1-866-680-2906.
          </p>

          <p>
            <strong>Do I have to participate?</strong> No. If you don&rsquo;t
            want to be in the study, just check the box that says &ldquo;I do
            not want my data to be used in research&rdquo; at the bottom of the
            screen before you click &ldquo;Continue with the Survey,&rdquo; and
            none of your answers to the survey questions will be used for the
            research.
          </p>

          <p>
            <strong>How will you store data?</strong> All confidential data we
            receive will be digital and will be kept in electronic spreadsheets
            stored in encrypted folders on password-protected computers or in
            password-protected databases. When we receive confidential data, it
            is immediately stripped of identifiable information. For example,
            names are replaced with numbers that nobody else knows. Identifiable
            data (like names) will not be shared with anyone outside the trained
            research team. All confidential data will be deleted when no longer
            needed for the study.
          </p>

          <p>
            <strong>How will results be used?</strong> After we finish our
            project, we will write reports describing what we have learned from
            working with you and your classmates. All your information will
            remain strictly confidential. We will present your school&rsquo;s
            data to your teacher and principal as well as to the broader
            research community without showing anybody&rsquo;s individual
            responses.
          </p>
          <p>
            If you understand the study and you are willing to participate, then
            you just need to continue to the survey. If you do not want to
            participate, please check the box next to the sentence, &ldquo;I do
            not want my data to be used in research,&rdquo; and then continue to
            the survey.
          </p>

          <p>
            Protocol Approval Date: 01/21/2019
          </p>

        </div>
        <div class="EpAssentButton">
          <button class="btn" ng-click="$ctrl.continue()">
            Continue With The Survey
          </button>
        </div>
        <div class="EpAssentReject">
          <label>
            I do <em>not</em> want my data to be used in research
            <input
              type="checkbox"
              ng-model="$ctrl.doesNotAssent"
            />
          </label>
        </div>
      </div>
    `,
    require: {
      parent: '^nepPresurvey',
    },
  });
};

export default presurveyEpAssent;
