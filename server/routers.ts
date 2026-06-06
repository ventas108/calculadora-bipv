import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";
import { z } from "zod";
import { listCustomPanels, createCustomPanel, updateCustomPanel, deleteCustomPanel, listBipvSimulations, getBipvSimulation, createBipvSimulation, deleteBipvSimulation, saveHourlyResults, getHourlyResults } from "./db";
import { extractPanelFromPDF } from "./pdfPanelExtractor";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  // Custom Panels CRUD
  customPanels: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return listCustomPanels(ctx.user.id);
    }),

    create: protectedProcedure
      .input(z.object({
        name: z.string().min(1).max(255),
        powerRating: z.number().positive(),
        efficiency: z.number().min(0).max(100),
        tempCoeff: z.number(),
        noct: z.number().min(30).max(80),
        area: z.number().positive(),
        degradationAnnual: z.number().min(0).max(5),
        voc: z.number().optional(),
        isc: z.number().optional(),
        vmp: z.number().optional(),
        imp: z.number().optional(),
        lengthMm: z.number().optional(),
        widthMm: z.number().optional(),
        weightKg: z.number().optional(),
        systemLoss: z.number().optional(),
        application: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        return createCustomPanel({
          userId: ctx.user.id,
          ...input,
        });
      }),

    update: protectedProcedure
      .input(z.object({
        id: z.number(),
        name: z.string().min(1).max(255).optional(),
        powerRating: z.number().positive().optional(),
        efficiency: z.number().min(0).max(100).optional(),
        tempCoeff: z.number().optional(),
        noct: z.number().min(30).max(80).optional(),
        area: z.number().positive().optional(),
        degradationAnnual: z.number().min(0).max(5).optional(),
        voc: z.number().optional(),
        isc: z.number().optional(),
        vmp: z.number().optional(),
        imp: z.number().optional(),
        lengthMm: z.number().optional(),
        widthMm: z.number().optional(),
        weightKg: z.number().optional(),
        systemLoss: z.number().optional(),
        application: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const { id, ...data } = input;
        return updateCustomPanel(id, ctx.user.id, data);
      }),

    delete: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        return deleteCustomPanel(input.id, ctx.user.id);
      }),

    /** Extraer parámetros de panel desde ficha técnica PDF */
    extractFromPDF: protectedProcedure
      .input(z.object({
        fileBase64: z.string().max(20_000_000), // ~15MB max en base64
        fileName: z.string().max(255),
      }))
      .mutation(async ({ input }) => {
        const pdfBuffer = Buffer.from(input.fileBase64, 'base64');
        if (pdfBuffer.length > 16 * 1024 * 1024) {
          throw new Error('El archivo PDF excede el límite de 16MB');
        }
        const extracted = await extractPanelFromPDF(pdfBuffer, input.fileName);
        return extracted;
      }),
  }),

  // BIPV Simulations CRUD (Persistencia del Orquestador IAM+Soiling)
  bipvSimulations: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return listBipvSimulations(ctx.user.id);
    }),

    get: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ ctx, input }) => {
        return getBipvSimulation(input.id, ctx.user.id);
      }),

    save: protectedProcedure
      .input(z.object({
        name: z.string().min(1).max(255),
        technology: z.string().max(100),
        generation: z.string().max(10),
        transparencia: z.number().min(0).max(1),
        eficienciaAjustada: z.number().min(0).max(1),
        areaM2: z.number().positive(),
        inclinacionFachada: z.number().min(0).max(180),
        azimutFachada: z.number().min(0).max(360),
        kBipv: z.number().min(0.5).max(3),
        transpositionModel: z.string().max(20),
        latitude: z.number().min(-90).max(90),
        longitude: z.number().min(-180).max(180),
        energiaAnualKwh: z.number(),
        energiaAnualKwhM2: z.number(),
        potenciaPicoW: z.number(),
        iluminacionPasivaAnualKwh: z.number(),
        irradianciaReflejadaAnualKwhM2: z.number(),
        perdidasSoilingAnualKwhM2: z.number(),
        perdidasTermicasAnualKwhM2: z.number(),
        iamPromedio: z.number(),
        soilingPromedio: z.number(),
        factorTermicoPromedio: z.number(),
        factorSombraPromedio: z.number(),
        horasSimuladas: z.number().int(),
        produccionMensualKwh: z.string(), // JSON array
        iluminacionMensualKwh: z.string(), // JSON array
        soilingConfig: z.string().optional(),
        notes: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        return createBipvSimulation({
          userId: ctx.user.id,
          ...input,
        });
      }),

    delete: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        return deleteBipvSimulation(input.id, ctx.user.id);
      }),

    /** Guardar simulación con resultados horarios completos */
    saveWithHourly: protectedProcedure
      .input(z.object({
        simulation: z.object({
          name: z.string().min(1).max(255),
          technology: z.string().max(100),
          generation: z.string().max(10),
          transparencia: z.number().min(0).max(1),
          eficienciaAjustada: z.number().min(0).max(1),
          areaM2: z.number().positive(),
          inclinacionFachada: z.number().min(0).max(180),
          azimutFachada: z.number().min(0).max(360),
          kBipv: z.number().min(0.5).max(3),
          transpositionModel: z.string().max(20),
          latitude: z.number().min(-90).max(90),
          longitude: z.number().min(-180).max(180),
          energiaAnualKwh: z.number(),
          energiaAnualKwhM2: z.number(),
          potenciaPicoW: z.number(),
          iluminacionPasivaAnualKwh: z.number(),
          irradianciaReflejadaAnualKwhM2: z.number(),
          perdidasSoilingAnualKwhM2: z.number(),
          perdidasTermicasAnualKwhM2: z.number(),
          iamPromedio: z.number(),
          soilingPromedio: z.number(),
          factorTermicoPromedio: z.number(),
          factorSombraPromedio: z.number(),
          horasSimuladas: z.number().int(),
          produccionMensualKwh: z.string(),
          iluminacionMensualKwh: z.string(),
          soilingConfig: z.string().optional(),
          notes: z.string().optional(),
        }),
        hourlyData: z.array(z.object({
          month: z.number().int().min(1).max(12),
          hourlyData: z.any(),
          monthlySummary: z.any(),
        })),
      }))
      .mutation(async ({ ctx, input }) => {
        // 1. Guardar resumen
        const sim = await createBipvSimulation({
          userId: ctx.user.id,
          ...input.simulation,
        });
        if (!sim) throw new Error('Failed to save simulation');
        // 2. Guardar datos horarios por mes
        await saveHourlyResults(sim.id, input.hourlyData);
        return sim;
      }),

    /** Obtener simulación con datos horarios */
    getWithHourly: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ ctx, input }) => {
        const sim = await getBipvSimulation(input.id, ctx.user.id);
        if (!sim) return null;
        const hourly = await getHourlyResults(sim.id);
        return { ...sim, hourlyResults: hourly };
      }),

    /** Comparar múltiples simulaciones */
    compare: protectedProcedure
      .input(z.object({ ids: z.array(z.number()).min(2).max(5) }))
      .query(async ({ ctx, input }) => {
        const results = [];
        for (const id of input.ids) {
          const sim = await getBipvSimulation(id, ctx.user.id);
          if (sim) results.push(sim);
        }
        return results;
      }),
  }),
});

export type AppRouter = typeof appRouter;
