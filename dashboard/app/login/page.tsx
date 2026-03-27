export default function LoginPage() {
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Admin login with password and TOTP</h2>
        <p>
          This v1 scaffold uses Auth.js credentials and is ready for a seeded admin account.
          In production, wire it to the `AdminUser` table and store encrypted TOTP secrets.
        </p>
      </section>

      <section className="panel">
        <form className="form" action="/api/auth/signin" method="post">
          <input className="input" name="email" placeholder="Admin email" type="email" required />
          <input className="input" name="password" placeholder="Password" type="password" required />
          <input className="input" name="totpCode" placeholder="6-digit TOTP code" type="text" />
          <button className="button" type="submit">Sign in</button>
        </form>
      </section>
    </div>
  );
}
