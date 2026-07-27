export interface StoredFacadeReport {
  id: string;
  facadeName: string;
  timestamp: number;
  data: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
    elevation: number;
    tilt: number;
    azimuth: number;
    area: number;
    panelPower: number;
    panelEfficiency: number;
    panelQuantity: number;
    annualProduction: number;
    capacityFactor: number;
    performanceRatio: number;
    systemLosses: number;
    paybackPeriod: number;
    roi10Year: number;
    roi25Year: number;
    annualFS: number;
    annualShadingLoss: number;
    annualPOA: number;
    annualPOANoShading: number;
    fsJunSolstice: number;
    fsDecSolstice: number;
  };
}
