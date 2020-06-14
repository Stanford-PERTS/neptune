## Testing

* wrote those unit tests
  - neptune-register-exists
  - neptune-register-new
  - neptune-register-pending
  - triton-register-exists
  - triton-register-new
  - triton-register-pending

## Neptune Migration

* ???

## Mandrill Templates

`triton-register-exists`

```html
<p>
+    {{#if program_name}}
+    Thank you for your interest in <em>{{program_name}}</em>!
+    {{else}}
     Thank you for your interest in PERTS <em>Copilot</em>!
+    {{/if}}
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
+    {{#if program_name}}
+    Thank you for your interest in <em>{{program_name}}</em>!
+    {{else}}
     Thank you for your interest in PERTS <em>Copilot</em>!
+    {{/if}}
</p>

<p>
    Please <a href="{{link}}">click here to confirm your email address and set up your account</a>.
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
  If you did not request this reset, please contact us immediately at <a href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
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
  If you did not request this reset, please contact us immediately at <a href="mailto:{{ contact_email_address }}">{{ contact_email_address }}</a>.
</p>

<p>
    <em>Sent by PERTS Copilot</em>
</p>
```

`triton-invite-exists`

```html
<p>
+    {{#if program_name}}
+    You&rsquo;ve been invited to join <em>{{ team_name }}</em> in <em>{{program_name}}</em>!
+    {{else}}
     You&rsquo;ve been invited to join <em>{{ team_name }}</em> on <em>Copilot</em>!
+    {{/if}}
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
  Welcome to PERTS <em>Copilot</em>!
</p>

<p>
+    {{#if program_name}}
+    {{ inviter_name }} ({{ inviter_email }}) has added you to <em>{{ team_name }}</em> in <em>{{program_name}}</em>.
+    {{else}}
     {{ inviter_name }} ({{ inviter_email }}) has added you to <em>{{ team_name }}</em>.
+    {{/if}}
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
