export const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;

export function validatePasswordStrength(value) {
  if (!value) return { valid: false, message: 'Password required' };
  const lengthOk = value.length >= 8;
  const hasLower = /[a-z]/.test(value);
  const hasUpper = /[A-Z]/.test(value);
  const hasNumber = /\d/.test(value);
  const hasSymbol = /[!@#$%^&*(),.?":{}|<>]/.test(value);

  const score = [lengthOk, hasLower, hasUpper, hasNumber, hasSymbol].reduce(
    (s, v) => s + (v ? 1 : 0),
    0
  );

  let message = 'Weak password';
  if (score >= 4) message = 'Strong password';
  else if (score === 3) message = 'Medium strength';

  return { valid: score >= 3, score, message };
}
