import Credentials from "next-auth/providers/credentials";
import NextAuth from "next-auth";
import bcrypt from "bcryptjs";
import { authenticator } from "otplib";
import { z } from "zod";

const credentialsSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  totpCode: z.string().length(6).optional()
});

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: {
    strategy: "jwt"
  },
  providers: [
    Credentials({
      credentials: {
        email: {},
        password: {},
        totpCode: {}
      },
      authorize: async (rawCredentials) => {
        const parsed = credentialsSchema.safeParse(rawCredentials);
        if (!parsed.success) {
          return null;
        }

        const seededEmail = process.env.ADMIN_EMAIL ?? "admin@example.com";
        const seededHash = process.env.ADMIN_PASSWORD_HASH ?? "";
        const seededTotp = process.env.ADMIN_TOTP_SECRET;

        if (parsed.data.email !== seededEmail) {
          return null;
        }

        const passwordOk = seededHash
          ? await bcrypt.compare(parsed.data.password, seededHash)
          : parsed.data.password === "changeme123";

        if (!passwordOk) {
          return null;
        }

        if (seededTotp && parsed.data.totpCode && !authenticator.check(parsed.data.totpCode, seededTotp)) {
          return null;
        }

        return {
          id: "admin",
          email: seededEmail,
          name: "InvoiceBot Admin"
        };
      }
    })
  ],
  pages: {
    signIn: "/login"
  }
});
