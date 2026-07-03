# Authentication & Two-Factor Authentication

---

## User roles

Every user has a `role` field (`accounts.User`) with three options:

| Role | `role` value | Access |
|---|---|---|
| Admin | `admin` | Full access — can create users, delete leads/clients, access all reports |
| Sales | `sales` | Can create and edit leads; cannot delete, cannot access billing |
| Accounts | `accounts` | Can create and edit clients and invoices; limited lead access |

`is_superuser=True` overrides all role checks and grants full access everywhere.

Set roles at **Django Admin → Accounts → Users**, or use the in-app **Users** page (`/accounts/users/`) — visible to admins only.

---

## Login

`/accounts/login/` — standard username + password form.

After login:
- If 2FA is **not** enabled → redirect to dashboard (`/`)
- If 2FA **is** enabled → `TwoFactorMiddleware` intercepts every request and redirects to `/accounts/2fa/verify/` until the TOTP code is verified for this session

---

## Two-Factor Authentication (TOTP)

CLRT uses **Time-based One-Time Passwords** (RFC 6238) via `pyotp`. Compatible with any TOTP app: Google Authenticator, Authy, 1Password, Bitwarden, etc.

### Enable 2FA

1. Go to **Profile** (`/accounts/profile/`) → click **Enable 2FA**
2. Scan the QR code with your authenticator app, or copy the manual secret and enter it
3. Enter the 6-digit code shown in the app to confirm
4. 2FA is now active — every login requires a code after the password step

### How it works

```
Login (password) → session created
        ↓
TwoFactorMiddleware checks every request:
  user.totp_enabled AND NOT session['2fa_verified']?
        ↓ yes
  → redirect to /accounts/2fa/verify/
        ↓ correct code entered
  session['2fa_verified'] = True
        ↓
  Normal access resumes
```

The middleware is registered in `MIDDLEWARE` after `AuthenticationMiddleware`:

```python
"accounts.middleware.TwoFactorMiddleware",
```

Exempt paths (never redirected):
- `/accounts/login/`
- `/accounts/logout/`
- `/accounts/2fa/verify/`
- `/accounts/2fa/setup/`

### Disable 2FA

1. Go to **Profile → Manage** (or `/accounts/2fa/setup/`)
2. Enter your current authenticator code in the **Disable 2FA** section
3. Click **Disable** and confirm

### Lost authenticator access

If a user loses their authenticator app, an admin must reset their 2FA via the Django shell:

```python
from accounts.models import User
u = User.objects.get(username="the_user")
u.totp_enabled = False
u.totp_secret = ""
u.save()
```

The user can then log in with just their password and re-enroll.

---

## Logout

Logout requires a POST request (Django 5.x security requirement). The sidebar uses a form with a CSRF token rather than a plain `<a>` link. Do **not** change this to a GET request.

```html
<form method="post" action="{% url 'accounts:logout' %}">
  {% csrf_token %}
  <button type="submit">Sign out</button>
</form>
```

---

## Dependencies

```
pyotp==2.10.0      # TOTP generation and verification
qrcode[pil]==8.2   # QR code image generation for setup page
```

Install with:
```bash
pip install pyotp "qrcode[pil]"
```
