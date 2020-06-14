## Testing

* can still register from yellowstone (changed CORS rules)
* new signature for User.create_reset_link

## Neptune Migration

* create mandrill templates to match those in repo (`/templates/emails`)
  - `neptune-register-exists`
  - `neptune-register-new`
  - `neptune-register-pending`
  - `neptune-invite-exists`
  - `neptune-invite-new`
  - `neptune-reset-exists`
  - `neptune-reset-not-found`
* check all uses of `User.create_reset_link`
* have client send new parameters
  - `domain`: current protocol and domain, e.g. `http:localhost:8080`
  - `template_prefix` "neptune"
* check user flow for each email template
* check that inviting from task or from org team screen works.

## Mandrill Templates

`triton-register-exists`

```html
<p>
    Thank you for your interest in the PERTS Engagement Project!
</p>

<p>
    You already have a PERTS account, all you need to do is
    <a href="{{link}}">log in</a>.
</p>

<p>
  If you did not request this email from PERTS, please contact us right away at
  <a href="mailto:{{contact_email_address}}">{{contact_email_address}}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-register-new`

```html
<p>
    Thank you for your interest in the PERTS Engagement Project!
</p>

<p>
    Please <a href="{{link}}">click here</a> to confirm your email address and set up your account.
</p>

<p>
  Please note that <strong>your link will expire in 48 hours</strong>, so
  let&rsquo;s get you set up right away!
</p>

<p>
  If you did not request this email from PERTS, please contact us right away at
  <a href="mailto:{{contact_email_address}}">{{contact_email_address}}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-register-pending`

```html
<!--
  This is the unusual case where a user has been invited and sent a link to
  set their password OR they went through the initial phase of registration to
  get a link, but in either case didn't USE that link. Instead, they attempt
  to register with the email address that has already been set up for them.
-->
<p>
    You&rsquo;ve already started the process of creating your PERTS account!
</p>

<p>
    Please <a href="{{link}}">click here to finish the process and confirm your account</a>.
</p>

<p>
  Please note that <strong>your link will expire in 48 hours</strong>, so
  let&rsquo;s get you set up right away!
</p>

<p>
  If you have any questions, please contact us at
  <a href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-reset-not-found`

```html
<p>
  A password reset was requested for this email address with PERTS. However,
  we have no record of this account.
</p>

<p>
  If you would like an account, please <a href="{{link}}">click here to
  register</a>.
</p>

<p>
  If you did not request this reset, please contact us immediately at <a
  href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-reset-exists`

```html
<p>
  A password reset was requested for this account with PERTS.
</p>

<p>
  Please <a href="{{link}}">click here to reset your password</a>.
</p>

<p>
  Please note that <strong>your link will expire in 48 hours</strong>, so
  let&rsquo;s get you set up right away!
</p>

<p>
  If you did not request this reset, please contact us immediately at <a
  href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-invite-exists`

```html
<p>
  You&rsquo;ve been invited to join {{ team.name }} on <em>Copilot</em>!
</p>

<p>
  You already have a PERTS account, so please <a href="{{link}}">log in</a> to get started.
</p>

<p>
  If you have any questions, you may contact us at
  <a href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-invite-new`

```html
<p>
  You&rsquo;ve been invited to join {{ team.name }} on <em>Copilot</em>!
</p>

<p>
  Please <a href="{{link}}">click here to create your account</a>.
</p>

<p>
  If you have any questions, you may contact us at
  <a href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

## Manrdill calls

Demonstrates using `global_merge_vars` to provide data to handlebars-based templates.

```json
{
  "key": "HItWZ4h8pOzJxcpG8zscoA",
  "template_name": "triton-register-exists",
  "template_content": [],
  "message": {
    "merge_language": "handlebars",
    "global_merge_vars": [
      {
        "content": "http://www.example.com",
        "name": "link"
      },
      {
        "content": "?foo=bar&baz=qux",
        "name": "query_string"
      },
      {
        "content": "contact@perts.net",
        "name": "contact_email_address"
      }
    ],
    "from_name": "PERTS",
    "text": null,
    "inline_css": false,
    "from_email": "support@perts.net",
    "to": [
      {
        "type": "to",
        "email": "perts01@mailinator.com"
      }
    ],
    "html": null
  }
}
```

Demonstrates that `global_merge_vars` and `merge_language` don't harm existing neptune calls.

```json
{
  "key": "HItWZ4h8pOzJxcpG8zscoA",
  "template_name": "cb17-loa-reminder",
  "template_content": [
    {
      "content": "Debbie Demo",
      "name": "liaison.name"
    },
    {
      "content": "HG17",
      "name": "project.program_label"
    }
  ],
  "message": {
    "merge_language": "handlebars",
    "global_merge_vars": [],
    "from_name": "PERTS",
    "text": null,
    "inline_css": false,
    "from_email": "support@perts.net",
    "to": [
      {
        "type": "to",
        "email": "perts01@mailinator.com"
      }
    ],
    "html": null
  }
}
```