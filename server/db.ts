import { eq, desc, and } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, customPanels, InsertCustomPanel, CustomPanel, bipvSimulations, InsertBipvSimulation, BipvSimulation, bipvHourlyResults, InsertBipvHourlyResult } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// ============================================================
// CUSTOM PANELS CRUD
// ============================================================

export async function listCustomPanels(userId: number): Promise<CustomPanel[]> {
  const db = await getDb();
  if (!db) return [];
  return db.select().from(customPanels).where(eq(customPanels.userId, userId));
}

export async function createCustomPanel(data: InsertCustomPanel): Promise<CustomPanel | null> {
  const db = await getDb();
  if (!db) return null;
  const result = await db.insert(customPanels).values(data);
  const insertId = result[0].insertId;
  const rows = await db.select().from(customPanels).where(eq(customPanels.id, insertId)).limit(1);
  return rows[0] ?? null;
}

export async function updateCustomPanel(id: number, userId: number, data: Partial<InsertCustomPanel>): Promise<CustomPanel | null> {
  const db = await getDb();
  if (!db) return null;
  const { userId: _, ...updateData } = data as any;
  await db.update(customPanels).set(updateData).where(eq(customPanels.id, id));
  const rows = await db.select().from(customPanels).where(eq(customPanels.id, id)).limit(1);
  if (rows.length === 0 || rows[0].userId !== userId) return null;
  return rows[0];
}

export async function deleteCustomPanel(id: number, userId: number): Promise<boolean> {
  const db = await getDb();
  if (!db) return false;
  // Verify ownership before delete
  const rows = await db.select().from(customPanels).where(eq(customPanels.id, id)).limit(1);
  if (rows.length === 0 || rows[0].userId !== userId) return false;
  await db.delete(customPanels).where(eq(customPanels.id, id));
  return true;
}

// ============================================================
// BIPV SIMULATIONS CRUD (Persistencia del Orquestador)
// ============================================================

export async function listBipvSimulations(userId: number): Promise<BipvSimulation[]> {
  const db = await getDb();
  if (!db) return [];
  return db.select().from(bipvSimulations)
    .where(eq(bipvSimulations.userId, userId))
    .orderBy(desc(bipvSimulations.createdAt));
}

export async function getBipvSimulation(id: number, userId: number): Promise<BipvSimulation | null> {
  const db = await getDb();
  if (!db) return null;
  const rows = await db.select().from(bipvSimulations).where(eq(bipvSimulations.id, id)).limit(1);
  if (rows.length === 0 || rows[0].userId !== userId) return null;
  return rows[0];
}

export async function createBipvSimulation(data: InsertBipvSimulation): Promise<BipvSimulation | null> {
  const db = await getDb();
  if (!db) return null;
  const result = await db.insert(bipvSimulations).values(data);
  const insertId = result[0].insertId;
  const rows = await db.select().from(bipvSimulations).where(eq(bipvSimulations.id, insertId)).limit(1);
  return rows[0] ?? null;
}

export async function deleteBipvSimulation(id: number, userId: number): Promise<boolean> {
  const db = await getDb();
  if (!db) return false;
  const rows = await db.select().from(bipvSimulations).where(eq(bipvSimulations.id, id)).limit(1);
  if (rows.length === 0 || rows[0].userId !== userId) return false;
  // Eliminar resultados horarios asociados
  await db.delete(bipvHourlyResults).where(eq(bipvHourlyResults.simulationId, id));
  await db.delete(bipvSimulations).where(eq(bipvSimulations.id, id));
  return true;
}

// ============================================================
// BIPV HOURLY RESULTS (Datos horarios por mes)
// ============================================================

export async function saveHourlyResults(simulationId: number, monthlyData: Array<{ month: number; hourlyData: unknown; monthlySummary: unknown }>): Promise<void> {
  const db = await getDb();
  if (!db) return;
  // Insertar 12 filas (una por mes)
  const rows: InsertBipvHourlyResult[] = monthlyData.map(m => ({
    simulationId,
    month: m.month,
    hourlyData: m.hourlyData,
    monthlySummary: m.monthlySummary,
  }));
  // Insert in batches to avoid packet size issues
  for (const row of rows) {
    await db.insert(bipvHourlyResults).values(row);
  }
}

export async function getHourlyResults(simulationId: number): Promise<Array<{ month: number; hourlyData: unknown; monthlySummary: unknown }>> {
  const db = await getDb();
  if (!db) return [];
  const rows = await db.select().from(bipvHourlyResults)
    .where(eq(bipvHourlyResults.simulationId, simulationId))
    .orderBy(bipvHourlyResults.month);
  return rows.map(r => ({ month: r.month, hourlyData: r.hourlyData, monthlySummary: r.monthlySummary }));
}

export async function getHourlyResultsByMonth(simulationId: number, month: number): Promise<{ hourlyData: unknown; monthlySummary: unknown } | null> {
  const db = await getDb();
  if (!db) return null;
  const rows = await db.select().from(bipvHourlyResults)
    .where(and(eq(bipvHourlyResults.simulationId, simulationId), eq(bipvHourlyResults.month, month)))
    .limit(1);
  if (rows.length === 0) return null;
  return { hourlyData: rows[0].hourlyData, monthlySummary: rows[0].monthlySummary };
}
