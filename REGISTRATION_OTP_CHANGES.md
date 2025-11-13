# Registration with Email OTP Verification - Changes Summary

## Overview

Updated the registration flow to require email verification via OTP (One-Time Password) sent to the user's email address. Also removed "Change Email" and "Setup 2FA" options from Settings menu.

## Backend Changes

### 1. `backend/main.py` - Updated Registration Flow

#### Added Import:

```python
import pyotp
```

#### Modified `/api/auth/register` endpoint:

- **Old Behavior**: User registered and immediately got access tokens
- **New Behavior**:
  - User registers but account is set to `is_active=False`
  - 6-digit OTP code generated using `pyotp`
  - OTP sent via email using `email_service.send_2fa_code_email()`
  - Returns success message asking user to check email
  - OTP valid for 10 minutes

#### Added New Endpoint `/api/auth/verify-otp`:

- **Method**: POST
- **Purpose**: Verify the OTP code sent during registration
- **Input**: `{ "email": "user@example.com", "otp": "123456" }`
- **Process**:
  1. Finds user by email
  2. Checks if user is already active
  3. Verifies OTP using `pyotp.TOTP` (10-minute window)
  4. Activates user account (`is_active=True`)
  5. Returns access & refresh tokens
- **Returns**: TokenResponse with access and refresh tokens

#### Added New Endpoint `/api/auth/resend-otp`:

- **Method**: POST
- **Purpose**: Resend OTP if user didn't receive it or it expired
- **Input**: `{ "email": "user@example.com" }`
- **Process**:
  1. Finds user by email
  2. Checks if user is inactive (needs verification)
  3. Generates new OTP
  4. Sends via email
- **Returns**: Success message

### 2. `backend/auth.py` - Updated Token Creation

#### Modified `create_token()` method:

```python
def create_token(self, data: dict, token_type: str, expires_minutes: Optional[int] = None) -> str:
```

- Added optional `expires_minutes` parameter
- Allows custom expiry times for tokens (used in password reset, email verification)
- Falls back to default expiry if not provided

## Frontend Changes

### 1. `frontend/src/pages/Register.js` - Two-Step Registration

#### New Features:

- **Step 1**: Registration Form (name, email, password, confirm password)
- **Step 2**: OTP Verification Form

#### Step 1 - Registration Form:

- User enters registration details
- On submit, calls `/api/auth/register`
- Shows success message
- Automatically moves to Step 2

#### Step 2 - OTP Verification:

- Shows email icon and message
- Large 6-digit OTP input field
- "Verify Email" button
- "Resend OTP" button
- "Back to Registration" button
- Input formatting: only digits, max 6 characters
- Centered display with letter spacing

#### Key Components:

```javascript
- useState for step tracking (1 or 2)
- useState for OTP input
- handleRegisterSubmit() - submits registration
- handleOtpSubmit() - verifies OTP and logs user in
- handleResendOtp() - requests new OTP
```

### 2. `frontend/src/components/Layout.js` - Removed Menu Items

#### Removed from User Profile Dropdown:

- ❌ "Change Email" menu item
- ✅ Kept "Profile"
- ✅ Kept "Manage Account"
- ✅ Kept "Change Password"
- ✅ Kept "Sign Out"

## User Flow

### New User Registration Flow:

1. **User visits `/register`**

   - Enters name, email, password, confirm password
   - Clicks "Sign up"

2. **Backend processes registration**

   - Validates data
   - Creates user with `is_active=False`
   - Generates 6-digit OTP (valid 10 minutes)
   - Sends OTP to user's email
   - Returns success message

3. **Frontend shows OTP verification screen**

   - User receives email with OTP code
   - User enters 6-digit code
   - Can resend OTP if needed

4. **Backend verifies OTP**

   - Validates OTP code
   - Activates user account (`is_active=True`)
   - Returns access & refresh tokens

5. **User redirected to mode selection**
   - Tokens stored in localStorage
   - User can now access the application

### OTP Email Details:

- **Subject**: "Your Verification Code - OneClouds"
- **Code**: 6-digit number (e.g., "542319")
- **Validity**: 10 minutes
- **Format**: HTML email with professional styling
- **Sender**: lakshya.dubeyji@gmail.com (OneClouds)

## Security Features

### OTP Security:

- ✅ 6-digit random code
- ✅ 10-minute expiry window
- ✅ Uses `pyotp` library (TOTP standard)
- ✅ Account inactive until verification
- ✅ Can resend OTP if expired

### Email Protection:

- ✅ Doesn't reveal if email exists (resend endpoint)
- ✅ Prevents unauthorized access to inactive accounts
- ✅ Email validation before registration

## What Was Removed

### From Settings Page:

1. **Change Email Section** - Users cannot change their email address
2. **Setup 2FA Section** - Two-factor authentication setup removed

### From Layout Menu:

1. **"Change Email" menu item** - Removed from user dropdown

## Testing the Changes

### Test Registration Flow:

1. **Start Backend**:

   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python main.py
   ```

2. **Start Frontend**:

   ```powershell
   cd frontend
   npm start
   ```

3. **Register New User**:

   - Go to http://localhost:3000/register
   - Fill in registration form
   - Click "Sign up"
   - Check email for OTP code
   - Enter 6-digit code
   - Click "Verify Email"
   - Should redirect to mode selection

4. **Test Resend OTP**:

   - After registration, wait or click "Resend OTP"
   - Check email for new code
   - Enter new code

5. **Test Invalid OTP**:

   - Enter wrong code
   - Should show error message

6. **Test Expired OTP**:
   - Wait 11 minutes after registration
   - Try to verify with old code
   - Should show "Invalid or expired OTP"
   - Click "Resend OTP" to get new code

### Test Settings Page:

1. **Check User Menu**:
   - Login to application
   - Click user profile (bottom-left)
   - Verify only these options appear:
     - Profile
     - Manage Account
     - Change Password
     - Sign Out
   - "Change Email" should NOT appear

## Dependencies

### Already Installed:

- ✅ `pyotp` - For OTP generation and verification
- ✅ `email_service` - For sending emails
- ✅ `@mui/icons-material` - For Email and CheckCircle icons

### If Missing, Install:

```powershell
# Backend
cd backend
pip install pyotp

# Frontend
cd frontend
npm install @mui/icons-material
```

## Configuration

### Email Settings (backend/.env):

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=lakshya.dubeyji@gmail.com
SMTP_PASSWORD=<your-16-char-app-password>
FROM_EMAIL=lakshya.dubeyji@gmail.com
```

Make sure Gmail app password is configured correctly!

## API Endpoints Summary

| Endpoint               | Method | Purpose                 | Input                 | Output          |
| ---------------------- | ------ | ----------------------- | --------------------- | --------------- |
| `/api/auth/register`   | POST   | Register new user       | email, name, password | Success message |
| `/api/auth/verify-otp` | POST   | Verify registration OTP | email, otp            | Tokens          |
| `/api/auth/resend-otp` | POST   | Resend OTP              | email                 | Success message |

## Files Modified

### Backend:

1. `backend/main.py` - Registration and OTP endpoints
2. `backend/auth.py` - Token creation with custom expiry

### Frontend:

1. `frontend/src/pages/Register.js` - Two-step registration
2. `frontend/src/components/Layout.js` - Removed menu items

## Next Steps

1. ✅ Test registration flow with real email
2. ✅ Verify OTP email arrives
3. ✅ Test OTP expiry (10 minutes)
4. ✅ Test resend OTP functionality
5. ✅ Verify Settings page doesn't show removed options
6. ⏳ Consider adding rate limiting on OTP endpoints
7. ⏳ Add OTP attempt counter (lock after 5 failed attempts)
8. ⏳ Add email verification status indicator

## Troubleshooting

### OTP Email Not Arriving:

1. Check backend logs for email sending errors
2. Verify Gmail app password in `.env`
3. Check spam folder
4. Verify SMTP settings

### OTP Verification Fails:

1. Check if OTP expired (>10 minutes old)
2. Verify OTP was entered correctly (6 digits)
3. Try resending OTP
4. Check backend logs for errors

### User Already Active Error:

- User may have already verified
- Try logging in instead of re-registering
- Check database: `SELECT * FROM users WHERE email='...'`

## Summary

✅ **Completed**:

- Email OTP verification during registration
- Two-step registration process (form → OTP)
- OTP resend functionality
- Removed "Change Email" from Settings and menu
- Removed "Setup 2FA" from Settings
- Updated token creation to support custom expiry
- Professional email templates for OTP

🎉 **Result**: Secure registration flow with email verification!
