import { type ReactNode, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useHealthCheck } from '@workspace/api-client-react';
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Check,
  ChevronRight,
  CircleAlert,
  Compass,
  FileText,
  Gauge,
  Layers3,
  Menu,
  Radio,
  Ruler,
  ShieldCheck,
  Sparkles,
  SunMedium,
  X,
  Zap,
} from 'lucide-react';
import { ErrorBoundary } from '@/components/error-boundary';
import NotFound from '@/pages/not-found';
import {
  Link,
  Route,
  Switch,
  useLocation,
  Router as WouterRouter,
} from 'wouter';

const queryClient = new QueryClient();

type Step = {
  number: string;
  title: string;
  detail: string;
  icon: typeof Compass;
  accent: string;
};

const steps: Step[] = [
  {
    number: '01',
    title: 'Contexto del sitio',
    detail: 'Ubicación, orientación y geometría de la envolvente.',
    icon: Compass,
    accent: 'bg-[#e6f0ec] text-[#28756f]',
  },
  {
    number: '02',
    title: 'Configuración BIPV',
    detail: 'Módulos, inversor y sistema de montaje por fachada.',
    icon: Layers3,
    accent: 'bg-[#f7ead0] text-[#a56b0b]',
  },
  {
    number: '03',
    title: 'Balance energético',
    detail: 'Producción anual con supuestos visibles y trazables.',
    icon: BarChart3,
    accent: 'bg-[#e9e8f0] text-[#515574]',
  },
  {
    number: '04',
    title: 'Decisión de proyecto',
    detail: 'Resultados listos para presentar, comparar y defender.',
    icon: FileText,
    accent: 'bg-[#f4e5df] text-[#9d5743]',
  },
];

function HealthBadge() {
  const health = useHealthCheck({
    query: {
      queryKey: ['/api/healthz'],
      refetchInterval: 30000,
    },
  });

  if (health.isLoading) {
    return (
      <div
        className="flex items-center gap-2 text-xs text-[#aebbb8]"
        data-testid="status-api-loading"
        aria-live="polite"
      >
        <span className="h-2 w-2 animate-pulse rounded-full bg-[#d3a146]" />
        Comprobando API
      </div>
    );
  }

  if (health.isError) {
    return (
      <div
        className="flex items-center gap-2 text-xs text-[#e4b5a5]"
        data-testid="status-api-error"
        aria-live="polite"
      >
        <CircleAlert className="h-3.5 w-3.5" aria-hidden="true" />
        API no disponible
      </div>
    );
  }

  const status = health.data?.status || 'operativa';
  return (
    <div
      className="flex items-center gap-2 text-xs text-[#b8d8c7]"
      data-testid="status-api-healthy"
      aria-live="polite"
    >
      <span className="pulse-dot h-2 w-2 rounded-full bg-[#8fc8a7]" />
      API {status.toLowerCase()}
    </div>
  );
}

function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3" data-testid="brand-mark">
      <div className="relative flex h-9 w-9 items-center justify-center rounded-[11px] bg-[#edaa2e] text-[#183038] shadow-[0_5px_18px_rgba(237,170,46,.22)]">
        <SunMedium className="h-5 w-5" strokeWidth={2.2} aria-hidden="true" />
        <span className="absolute bottom-[5px] right-[6px] h-1.5 w-1.5 rounded-full bg-[#28756f]" />
      </div>
      {!compact && (
        <div className="leading-none">
          <div className="text-[14px] font-extrabold tracking-[-0.03em] text-[#f8f0df]">
            BIPV <span className="text-[#eab04b]">Colombia</span>
          </div>
          <div className="mt-1 font-mono-ui text-[8px] uppercase tracking-[0.2em] text-[#8faaa4]">
            instrumento de diseño
          </div>
        </div>
      )}
    </div>
  );
}

function Sidebar({ mobileOpen, onClose }: { mobileOpen: boolean; onClose: () => void }) {
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-[#10262c]/50 backdrop-blur-sm transition-opacity lg:hidden ${
          mobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[258px] flex-col bg-[#183038] px-5 py-6 text-[#f8f0df] transition-transform duration-300 lg:relative lg:z-10 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Navegación principal"
      >
        <div className="flex items-center justify-between">
          <Link href="/" className="rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-[#edaa2e]" data-testid="link-home-brand">
            <BrandMark />
          </Link>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-[#9bb0ab] hover:bg-[#24464c] hover:text-white lg:hidden"
            aria-label="Cerrar navegación"
            data-testid="button-close-navigation"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-14">
          <p className="px-3 font-mono-ui text-[10px] uppercase tracking-[0.18em] text-[#78938e]">
            espacio de trabajo
          </p>
          <nav className="mt-3 space-y-1" aria-label="Secciones">
            <a
              href="#inicio"
              onClick={onClose}
              className="flex items-center gap-3 rounded-xl bg-[#2a4b50] px-3 py-3 text-sm font-semibold text-[#f8f0df] shadow-[inset_3px_0_0_#edaa2e] outline-none transition-colors hover:bg-[#31565a] focus-visible:ring-2 focus-visible:ring-[#edaa2e]"
              data-testid="link-navigation-overview"
            >
              <Gauge className="h-[17px] w-[17px] text-[#edaa2e]" aria-hidden="true" />
              Vista general
            </a>
            <a
              href="#proceso"
              onClick={onClose}
              className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-[#b4c5c0] outline-none transition-colors hover:bg-[#24464c] hover:text-white focus-visible:ring-2 focus-visible:ring-[#edaa2e]"
              data-testid="link-navigation-process"
            >
              <Ruler className="h-[17px] w-[17px]" aria-hidden="true" />
              Cómo trabajamos
            </a>
            <a
              href="#criterios"
              onClick={onClose}
              className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-[#b4c5c0] outline-none transition-colors hover:bg-[#24464c] hover:text-white focus-visible:ring-2 focus-visible:ring-[#edaa2e]"
              data-testid="link-navigation-criteria"
            >
              <ShieldCheck className="h-[17px] w-[17px]" aria-hidden="true" />
              Criterios de confianza
            </a>
          </nav>
        </div>

        <div className="mt-auto border-t border-[#355257] pt-5">
          <div className="flex items-center justify-between">
            <span className="font-mono-ui text-[10px] uppercase tracking-[0.15em] text-[#78938e]">sistema</span>
            <HealthBadge />
          </div>
          <p className="mt-3 max-w-[190px] text-xs leading-5 text-[#78938e]">
            Datos y supuestos visibles para decisiones técnicas defendibles.
          </p>
          <div className="mt-6 flex items-center gap-2 text-[11px] text-[#78938e]">
            <span className="font-mono-ui">v0.1</span>
            <span className="h-1 w-1 rounded-full bg-[#54736f]" />
            <span>Colombia</span>
          </div>
        </div>
      </aside>
    </>
  );
}

function WorkflowCard({
  step,
  index,
  active,
  onSelect,
}: {
  step: Step;
  index: number;
  active: boolean;
  onSelect: () => void;
}) {
  const Icon = step.icon;
  return (
    <button
      type="button"
      className={`group flex w-full items-start gap-4 rounded-2xl border p-4 text-left transition-all duration-300 focus-visible:ring-2 focus-visible:ring-[#28756f] focus-visible:ring-offset-2 ${
        active
          ? 'border-[#dba541] bg-[#fff9ed] shadow-[0_10px_26px_rgba(83,66,32,.09)]'
          : 'border-[#e2dccf] bg-[#fcfaf5] hover:-translate-y-0.5 hover:border-[#c8b98f] hover:bg-[#fffdf8]'
      }`}
      onClick={onSelect}
      data-testid={`button-workflow-step-${index + 1}`}
      aria-pressed={active}
    >
      <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${step.accent}`}>
        <Icon className="h-[19px] w-[19px]" aria-hidden="true" />
      </span>
      <span className="min-w-0">
        <span className="flex items-center gap-2">
          <span className="font-mono-ui text-[10px] font-medium tracking-[0.12em] text-[#9a8f7b]">{step.number}</span>
          <span className="truncate text-[14px] font-bold text-[#19363a]">{step.title}</span>
        </span>
        <span className="mt-1 block text-[12px] leading-5 text-[#71807c]">{step.detail}</span>
      </span>
      <ChevronRight
        className={`ml-auto mt-1 h-4 w-4 shrink-0 transition-transform ${active ? 'translate-x-0.5 text-[#b17918]' : 'text-[#b9b1a3] group-hover:translate-x-0.5'}`}
        aria-hidden="true"
      />
    </button>
  );
}

function Home() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [started, setStarted] = useState(false);

  const beginAnalysis = () => {
    setStarted(true);
    setActiveStep(0);
    document.getElementById('proceso')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="grain flex min-h-[100dvh] bg-[#f4f0e6]" id="inicio">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <main className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex h-[74px] items-center justify-between border-b border-[#e3ddcf]/90 bg-[#f4f0e6]/90 px-5 backdrop-blur-xl sm:px-8 lg:px-12">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-[#31565a] hover:bg-[#e6e0d2] lg:hidden"
            aria-label="Abrir navegación"
            data-testid="button-open-navigation"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <div className="hidden items-center gap-2 text-xs text-[#77817e] sm:flex">
            <span className="font-mono-ui text-[10px] uppercase tracking-[0.16em]">proyecto sin seleccionar</span>
            <span className="h-1 w-1 rounded-full bg-[#d5a13c]" />
            <span>Vista general</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden rounded-full border border-[#ded5c3] bg-[#f9f6ed] px-3 py-1.5 text-[11px] font-semibold text-[#5f716c] sm:block" data-testid="text-location">
              Colombia · CREG
            </div>
            <button
              type="button"
              onClick={beginAnalysis}
              className="flex items-center gap-2 rounded-lg bg-[#28756f] px-3.5 py-2 text-xs font-bold text-[#fbf6ea] shadow-[0_4px_14px_rgba(40,117,111,.18)] transition-all hover:-translate-y-0.5 hover:bg-[#1e625d] focus-visible:ring-2 focus-visible:ring-[#28756f] focus-visible:ring-offset-2"
              data-testid="button-header-start-analysis"
            >
              <Zap className="h-3.5 w-3.5 fill-current" aria-hidden="true" />
              <span className="hidden sm:inline">Iniciar análisis</span>
              <span className="sm:hidden">Iniciar</span>
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1360px] px-5 pb-16 pt-8 sm:px-8 lg:px-12 lg:pt-12">
          <section className="rise-in grid-paper relative overflow-hidden rounded-[28px] border border-[#d9d2c2] bg-[#e8eee8] px-6 py-10 sm:px-10 sm:py-12 lg:px-14 lg:py-16" aria-labelledby="hero-title">
            <div className="pointer-events-none absolute -right-16 -top-24 h-[330px] w-[330px] rounded-full border-[1px] border-[#b8cec3] opacity-80" />
            <div className="pointer-events-none absolute -right-4 -top-12 h-[230px] w-[230px] rounded-full border-[1px] border-[#c2d5cb] opacity-80" />
            <div className="pointer-events-none absolute right-10 top-10 h-3 w-3 rounded-full bg-[#e4a835] shadow-[0_0_0_8px_rgba(228,168,53,.12)]" />
            <div className="relative max-w-[735px]">
              <div className="rise-in rise-in-delay-1 flex items-center gap-2 font-mono-ui text-[10px] font-medium uppercase tracking-[0.22em] text-[#28756f]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#e4a835]" />
                Instrumento para diseño solar
              </div>
              <h1 id="hero-title" className="rise-in rise-in-delay-1 mt-5 text-[clamp(2.65rem,6vw,5.7rem)] leading-[.92] tracking-[-0.045em] text-[#18363a]">
                De la idea de sitio a una <span className="font-display italic text-[#28756f]">decisión solar.</span>
              </h1>
              <p className="rise-in rise-in-delay-2 mt-6 max-w-[570px] text-[15px] leading-7 text-[#5c706b] sm:text-[17px]">
                Calcula el potencial fotovoltaico integrado de tu proyecto con un flujo claro, supuestos trazables y resultados que resisten la mesa de diseño.
              </p>
              <div className="rise-in rise-in-delay-3 mt-8 flex flex-col items-start gap-4 sm:flex-row sm:items-center">
                <button
                  type="button"
                  onClick={beginAnalysis}
                  className="group flex items-center gap-3 rounded-xl bg-[#edaa2e] px-5 py-3.5 text-[13px] font-extrabold text-[#183038] shadow-[0_10px_24px_rgba(191,132,27,.18)] transition-all hover:-translate-y-0.5 hover:bg-[#f2b63e] focus-visible:ring-2 focus-visible:ring-[#a56b0b] focus-visible:ring-offset-2"
                  data-testid="button-start-analysis"
                >
                  Comenzar un análisis
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                </button>
                <a
                  href="#criterios"
                  className="flex items-center gap-2 px-1 py-2 text-[13px] font-bold text-[#28756f] underline decoration-[#a8c5bb] underline-offset-4 transition-colors hover:text-[#183038] focus-visible:ring-2 focus-visible:ring-[#28756f]"
                  data-testid="link-hero-criteria"
                >
                  Conoce los criterios
                  <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
                </a>
              </div>
            </div>
            <div className="absolute bottom-8 right-8 hidden w-[185px] text-right lg:block">
              <div className="font-mono-ui text-[10px] uppercase tracking-[0.17em] text-[#72928a]">lectura de campo</div>
              <div className="mt-3 text-[12px] leading-5 text-[#67817a]">Cada resultado conserva el porqué detrás del número.</div>
            </div>
          </section>

          <section className="rise-in rise-in-delay-2 mt-10 grid gap-5 border-b border-[#ded7c8] pb-10 sm:grid-cols-3" aria-label="Indicadores de la plataforma">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-lg bg-[#f8e8c8] p-2 text-[#a56b0b]"><SunMedium className="h-4 w-4" aria-hidden="true" /></div>
              <div><div className="font-mono-ui text-[10px] uppercase tracking-[0.13em] text-[#a19a8c]">radiación local</div><div className="mt-1 text-[13px] font-bold text-[#304b4b]">Contexto colombiano</div></div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-lg bg-[#dcece5] p-2 text-[#28756f]"><ShieldCheck className="h-4 w-4" aria-hidden="true" /></div>
              <div><div className="font-mono-ui text-[10px] uppercase tracking-[0.13em] text-[#a19a8c]">trazabilidad</div><div className="mt-1 text-[13px] font-bold text-[#304b4b]">Supuestos visibles</div></div>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-lg bg-[#e7e6ef] p-2 text-[#595f84]"><Radio className="h-4 w-4" aria-hidden="true" /></div>
              <div><div className="font-mono-ui text-[10px] uppercase tracking-[0.13em] text-[#a19a8c]">estado en vivo</div><div className="mt-1 text-[13px] font-bold text-[#304b4b]">API conectada</div></div>
            </div>
          </section>

          <section id="proceso" className="scroll-mt-24 py-14 lg:py-20" aria-labelledby="process-title">
            <div className="grid gap-10 lg:grid-cols-[.75fr_1.25fr] lg:gap-20">
              <div>
                <div className="font-mono-ui text-[10px] font-medium uppercase tracking-[0.2em] text-[#ae7a23]">el recorrido</div>
                <h2 id="process-title" className="mt-4 max-w-[420px] text-[clamp(2rem,4vw,3.35rem)] leading-[.98] tracking-[-0.04em] text-[#19363a]">
                  Cuatro lecturas para una misma decisión.
                </h2>
                <p className="mt-5 max-w-[380px] text-[14px] leading-6 text-[#71807c]">
                  La herramienta acompaña el razonamiento técnico en lugar de esconderlo. Selecciona una etapa para ver qué se pone bajo la lupa.
                </p>
                <div className="mt-8 flex items-center gap-2 text-[11px] text-[#79908b]">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#28756f] text-[10px] font-bold text-[#f7f1e5]">{activeStep + 1}</span>
                  <span data-testid="text-active-step">de {steps.length} etapas activas</span>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {steps.map((step, index) => (
                  <WorkflowCard
                    key={step.number}
                    step={step}
                    index={index}
                    active={activeStep === index}
                    onSelect={() => setActiveStep(index)}
                  />
                ))}
              </div>
            </div>
            {started && (
              <div className="rise-in mt-6 flex items-center gap-3 rounded-xl border border-[#c3ddd0] bg-[#edf7f1] px-4 py-3 text-[13px] text-[#286b60]" role="status" data-testid="status-analysis-started">
                <Check className="h-4 w-4" aria-hidden="true" />
                <span><strong>Análisis preparado.</strong> Comienza definiendo el contexto del sitio.</span>
              </div>
            )}
          </section>

          <section id="criterios" className="scroll-mt-24 border-t border-[#ded7c8] py-14 lg:py-20" aria-labelledby="criteria-title">
            <div className="grid gap-10 lg:grid-cols-[1fr_1fr] lg:items-end">
              <div>
                <div className="font-mono-ui text-[10px] font-medium uppercase tracking-[0.2em] text-[#ae7a23]">diseñado para confiar</div>
                <h2 id="criteria-title" className="mt-4 max-w-[520px] text-[clamp(2rem,4vw,3.2rem)] leading-[.98] tracking-[-0.04em] text-[#19363a]">
                  No entregamos una caja negra.
                </h2>
              </div>
              <p className="max-w-[460px] text-[14px] leading-6 text-[#71807c]">
                Un análisis útil no es solo el resultado final. Es poder explicar de dónde salió, qué variables lo mueven y qué tan preparado está el proyecto para el siguiente paso.
              </p>
            </div>
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              <article className="rounded-2xl bg-[#183038] p-6 text-[#f7f1e5] md:col-span-2">
                <div className="flex items-start justify-between">
                  <div className="rounded-xl bg-[#285158] p-2.5 text-[#e9b64b]"><BookOpen className="h-5 w-5" aria-hidden="true" /></div>
                  <span className="font-mono-ui text-[10px] uppercase tracking-[0.17em] text-[#80a39b]">01 / criterio</span>
                </div>
                <h3 className="mt-10 text-2xl tracking-[-0.03em]">Ver el supuesto cambia la conversación.</h3>
                <p className="mt-3 max-w-[510px] text-[13px] leading-6 text-[#a8beb8]">Radiación, pérdidas y configuración no desaparecen detrás de un número. Se muestran en el lugar donde pueden ser revisados.</p>
              </article>
              <article className="rounded-2xl border border-[#dfd7c7] bg-[#fbf8f0] p-6">
                <div className="flex items-start justify-between">
                  <div className="rounded-xl bg-[#f8e8c8] p-2.5 text-[#a56b0b]"><Sparkles className="h-5 w-5" aria-hidden="true" /></div>
                  <span className="font-mono-ui text-[10px] uppercase tracking-[0.17em] text-[#ad9c7d]">02 / lectura</span>
                </div>
                <h3 className="mt-10 text-2xl tracking-[-0.03em] text-[#19363a]">Menos ruido. Más criterio.</h3>
                <p className="mt-3 text-[13px] leading-6 text-[#71807c]">Una interfaz con el ritmo de una mesa de diseño: densa cuando hace falta, serena siempre.</p>
              </article>
            </div>
          </section>

          <footer className="flex flex-col gap-5 border-t border-[#ded7c8] pt-7 text-[11px] text-[#89938e] sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#e5a42d] text-[#183038]"><SunMedium className="h-3.5 w-3.5" aria-hidden="true" /></div>
              <span data-testid="text-footer-brand">Calculadora BIPV Colombia</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="font-mono-ui">v0.1.0</span>
              <span>Una herramienta para diseñar con el sol.</span>
            </div>
          </footer>
        </div>
      </main>
    </div>
  );
}

function Router() {
  return (
    <RoutedErrorBoundary>
      <Switch>
        <Route path="/" component={Home} />
        <Route component={NotFound} />
      </Switch>
    </RoutedErrorBoundary>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
        <Router />
      </WouterRouter>
    </QueryClientProvider>
  );
}

export default App;