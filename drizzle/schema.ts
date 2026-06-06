import { int, float, mysqlEnum, mysqlTable, text, timestamp, varchar, json } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// ============================================================
// PANELES PERSONALIZADOS BIPV
// ============================================================

export const customPanels = mysqlTable("custom_panels", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  powerRating: float("powerRating").notNull(),
  efficiency: float("efficiency").notNull(),
  tempCoeff: float("tempCoeff").notNull(),
  noct: float("noct").notNull(),
  area: float("area").notNull(),
  degradationAnnual: float("degradationAnnual").notNull(),
  voc: float("voc"),
  isc: float("isc"),
  vmp: float("vmp"),
  imp: float("imp"),
  lengthMm: float("lengthMm"),
  widthMm: float("widthMm"),
  weightKg: float("weightKg"),
  systemLoss: float("systemLoss"),
  application: text("application"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type CustomPanel = typeof customPanels.$inferSelect;
export type InsertCustomPanel = typeof customPanels.$inferInsert;

// ============================================================
// SIMULACIONES BIPV IAM+SOILING (Persistencia del Orquestador)
// ============================================================

export const bipvSimulations = mysqlTable("bipv_simulations", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  /** Nombre descriptivo de la simulación */
  name: varchar("name", { length: 255 }).notNull(),
  /** Tecnología BIPV usada */
  technology: varchar("technology", { length: 100 }).notNull(),
  /** Generación (1G, 2G, 3G) */
  generation: varchar("generation", { length: 10 }).notNull(),
  /** Nivel de transparencia (0-1) */
  transparencia: float("transparencia").notNull(),
  /** Eficiencia STC ajustada por transparencia */
  eficienciaAjustada: float("eficienciaAjustada").notNull(),
  /** Área de fachada en m² */
  areaM2: float("areaM2").notNull(),
  /** Inclinación de la fachada en grados */
  inclinacionFachada: float("inclinacionFachada").notNull(),
  /** Azimut de la fachada en grados */
  azimutFachada: float("azimutFachada").notNull(),
  /** Factor k_bipv de montaje térmico */
  kBipv: float("kBipv").notNull(),
  /** Modelo de transposición usado */
  transpositionModel: varchar("transpositionModel", { length: 20 }).notNull(),
  /** Latitud de la ubicación */
  latitude: float("latitude").notNull(),
  /** Longitud de la ubicación */
  longitude: float("longitude").notNull(),
  // --- Resultados ---
  /** Energía anual generada (kWh) */
  energiaAnualKwh: float("energiaAnualKwh").notNull(),
  /** Energía anual por m² (kWh/m²) */
  energiaAnualKwhM2: float("energiaAnualKwhM2").notNull(),
  /** Potencia pico (W) */
  potenciaPicoW: float("potenciaPicoW").notNull(),
  /** Iluminación pasiva anual (kWh) */
  iluminacionPasivaAnualKwh: float("iluminacionPasivaAnualKwh").notNull(),
  // --- Pérdidas ópticas ---
  /** Pérdida por reflexión geométrica IAM (kWh/m²) */
  irradianciaReflejadaAnualKwhM2: float("irradianciaReflejadaAnualKwhM2").notNull(),
  /** Pérdida por suciedad (kWh/m²) */
  perdidasSoilingAnualKwhM2: float("perdidasSoilingAnualKwhM2").notNull(),
  /** Pérdida por temperatura (kWh/m²) */
  perdidasTermicasAnualKwhM2: float("perdidasTermicasAnualKwhM2").notNull(),
  // --- Factores promedio ---
  iamPromedio: float("iamPromedio").notNull(),
  soilingPromedio: float("soilingPromedio").notNull(),
  factorTermicoPromedio: float("factorTermicoPromedio").notNull(),
  factorSombraPromedio: float("factorSombraPromedio").notNull(),
  /** Horas simuladas */
  horasSimuladas: int("horasSimuladas").notNull(),
  /** Producción mensual (JSON array de 12 valores kWh) */
  produccionMensualKwh: text("produccionMensualKwh").notNull(),
  /** Iluminación mensual (JSON array de 12 valores kWh) */
  iluminacionMensualKwh: text("iluminacionMensualKwh").notNull(),
  /** Configuración de soiling usada (JSON) */
  soilingConfig: text("soilingConfig"),
  /** Notas del usuario */
  notes: text("notes"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type BipvSimulation = typeof bipvSimulations.$inferSelect;
export type InsertBipvSimulation = typeof bipvSimulations.$inferInsert;

// ============================================================
// RESULTADOS HORARIOS BIPV (almacenados como JSON por mes)
// Cada simulación genera 12 filas (una por mes) con ~730 registros horarios cada una
// ============================================================

export const bipvHourlyResults = mysqlTable("bipv_hourly_results", {
  id: int("id").autoincrement().primaryKey(),
  /** FK a bipv_simulations.id */
  simulationId: int("simulationId").notNull(),
  /** Mes (1-12) */
  month: int("month").notNull(),
  /** JSON array de resultados horarios del mes */
  hourlyData: json("hourlyData").notNull(),
  /** Resumen del mes: energía total, horas sol, pérdidas */
  monthlySummary: json("monthlySummary").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type BipvHourlyResult = typeof bipvHourlyResults.$inferSelect;
export type InsertBipvHourlyResult = typeof bipvHourlyResults.$inferInsert;