import { AuthError } from "next-auth";
import { redirect } from "next/navigation";
import { auth, signIn } from "../../lib/auth";

async function loginAction(formData: FormData) {
  "use server";

  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const totpCode = String(formData.get("totpCode") ?? "").trim();

  try {
    await signIn("credentials", {
      email,
      password,
      totpCode,
      redirectTo: "/"
    });
  } catch (error) {
    if (error instanceof AuthError) {
      redirect(`/login?error=${encodeURIComponent("Incorrect email, password, or TOTP code.")}`);
    }
    throw error;
  }
}

export default async function LoginPage({
  searchParams
}: {
  searchParams?: { error?: string };
}) {
  const session = await auth();
  if (session?.user) {
    redirect("/");
  }

  const error = searchParams?.error;

  return (
    <div className="auth-shell">
      <section className="auth-card">
        <span className="topbarEyebrow">InvoiceBot Admin</span>
        <h2>Admin login</h2>
        <p>
          Sign in with your seeded admin credentials. This dashboard is private and should only
          be used by approved operators.
        </p>

        {error ? (
          <div className="notice auth-error-notice">{error}</div>
        ) : null}

        <form className="form" action={loginAction}>
          <input className="input" name="email" placeholder="Admin email" type="email" required />
          <input className="input" name="password" placeholder="Password" type="password" required />
          <input className="input" name="totpCode" placeholder="6-digit TOTP code" type="text" inputMode="numeric" />
          <button className="button" type="submit">Sign in</button>
        </form>
      </section>
    </div>
  );
}
