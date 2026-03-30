import { Pool } from "pg";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../generated/prisma/client";

const connectionString = process.env.DATABASE_URL;
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient; prismaPool?: Pool };

let prismaClient: PrismaClient;

if (!connectionString) {
  prismaClient = new Proxy(
    {},
    {
      get() {
        throw new Error("DATABASE_URL is required for Prisma");
      }
    }
  ) as PrismaClient;
} else {
  const pool =
    globalForPrisma.prismaPool ??
    new Pool({
      connectionString,
    });

  const adapter = new PrismaPg(pool);

  prismaClient =
    globalForPrisma.prisma ??
    new PrismaClient({
      adapter,
      log: ["warn", "error"]
    });

  if (process.env.NODE_ENV !== "production") {
    globalForPrisma.prisma = prismaClient;
    globalForPrisma.prismaPool = pool;
  }
}

export const prisma = prismaClient;
