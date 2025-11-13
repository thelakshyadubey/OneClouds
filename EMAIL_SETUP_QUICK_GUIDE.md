# Quick Setup Guide - Email Authentication

## Step 1: Gmail App Password Setup

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Navigate to **Security** → **App passwords**
4. Create new app password:
   - App: Mail
   - Device: Other (OneClouds Backend)
5. Copy the 16-character password (format: xxxx-xxxx-xxxx-xxxx)

## Step 2: Update Backend .env File

Open `backend/.env` and update the SMTP_PASSWORD:

```env
SMTP_PASSWORD=your-16-character-app-password-here
```

Replace `your-16-character-app-password-here` with the password from Step 1 (remove spaces).

## Step 3: Install Backend Dependencies (if needed)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Step 4: Test Email Service

Run this Python command to test email sending:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from backend.email_service import email_service; result = email_service.send_password_reset_email('your-test-email@example.com', 'test-token-123'); print('Email sent!' if result else 'Email failed!')"
```

Replace `your-test-email@example.com` with your actual email to receive a test email.

## Step 5: Start Backend Server

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

Backend should be running on http://localhost:8000

## Step 6: Start Frontend Server

```powershell
cd frontend
npm start
```

Frontend should be running on http://localhost:3000

## Step 7: Test the Flow

### Test Forgot Password:

1. Go to http://localhost:3000/login
2. Click "Forgot your password?"
3. Enter your email address
4. Check your email inbox for password reset link
5. Click the link in the email
6. Enter new password (twice)
7. Submit and verify redirect to login

### Test Password Change Notification:

1. Login to the app
2. Go to Settings
3. Change your password
4. Check your email for "Password Changed" notification

### Test Email Change Verification:

1. Login to the app
2. Go to Settings
3. Enter new email address
4. Check NEW email address for verification link
5. Click link to verify

## Troubleshooting

### Emails not arriving?

**Check console logs:**

```powershell
# In backend terminal, look for errors like:
# "Failed to send email" or "SMTP error"
```

**Test SMTP connection:**

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python
```

```python
import smtplib
from email.mime.text import MIMEText
from backend.config import settings

msg = MIMEText("Test email from OneClouds")
msg["Subject"] = "Test"
msg["From"] = settings.FROM_EMAIL
msg["To"] = "your-email@example.com"

with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
    server.starttls()
    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    server.send_message(msg)
    print("Email sent successfully!")
```

**Common issues:**

- ❌ Wrong app password → Regenerate in Google Account
- ❌ 2FA not enabled → Enable in Google Account Security
- ❌ Firewall blocking port 587 → Allow in firewall settings
- ❌ Emails in spam → Mark as "Not Spam" and add to contacts

### Frontend errors?

**Check console in browser (F12):**

- Look for 404 errors on `/api/auth/forgot-password`
- Check CORS errors (should not happen on localhost)
- Verify API calls are going to `http://localhost:8000`

**Verify frontend config:**

```javascript
// frontend/src/config.js should have:
export const API_BASE_URL = "http://localhost:8000";
```

### Backend errors?

**Check FastAPI console:**

- Look for import errors (email_service)
- Check JWT token errors
- Verify database connection

**Common fixes:**

```powershell
# Reinstall dependencies
cd backend
pip install --upgrade -r requirements.txt

# Recreate database (if schema changed)
python create_db.py
```

## Testing Checklist

Quick tests to verify everything works:

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can navigate to http://localhost:3000/forgot-password
- [ ] Can submit email on forgot password page
- [ ] Receive password reset email within 1 minute
- [ ] Email link redirects to reset password page
- [ ] Can reset password successfully
- [ ] Redirected to login page after reset
- [ ] Can login with new password
- [ ] Password change sends notification email
- [ ] Email change sends verification email

## Production Deployment Notes

When deploying to production:

1. **Update FRONTEND_URL in backend/.env:**

   ```env
   FRONTEND_URL=https://your-production-domain.com
   ```

2. **Use environment variables (don't commit .env):**

   - Add `.env` to `.gitignore`
   - Set environment variables in hosting platform
   - Never commit SMTP_PASSWORD to Git

3. **Consider using a dedicated email service:**

   - SendGrid (free tier: 100 emails/day)
   - AWS SES (cheap, reliable)
   - Mailgun (developer-friendly)
   - Keep Gmail for development only

4. **Add email monitoring:**

   - Track delivery rates
   - Monitor bounce rates
   - Set up alerts for failures

5. **Enable SPF and DKIM:**
   - Required for production email delivery
   - Prevents emails from going to spam
   - Configured in domain DNS settings

## Support

If you encounter issues:

1. Check `EMAIL_AUTHENTICATION_SUMMARY.md` for detailed documentation
2. Review backend console logs for errors
3. Test SMTP connection manually (see Troubleshooting section)
4. Verify all environment variables are set correctly
5. Check Gmail account hasn't hit daily sending limits (500 emails/day)

## Done! 🎉

Your email authentication system is now ready to use. Test all flows thoroughly before deploying to production.
