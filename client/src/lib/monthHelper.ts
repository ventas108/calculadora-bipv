/**
 * Normaliza cualquier formato de entrada de mes (número 1-12, nombre en español, inglés,
 * abreviaturas, etc.) a la abreviatura estándar de 3 letras en español:
 * ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
 */
export function normalizeMonthToAbbr(monthInput: any): string {
  if (monthInput === undefined || monthInput === null) return 'Ene';
  
  const str = String(monthInput).trim().toLowerCase();
  if (!str) return 'Ene';

  // Si es un número del 1 al 12
  const num = parseInt(str, 10);
  const MONTHS_SPANISH = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  if (!isNaN(num) && num >= 1 && num <= 12) {
    return MONTHS_SPANISH[num - 1];
  }

  // Mapeo exhaustivo para inglés/español
  const mappings: Record<string, string> = {
    // Español
    'ene': 'Ene', 'enero': 'Ene',
    'feb': 'Feb', 'febrero': 'Feb',
    'mar': 'Mar', 'marzo': 'Mar',
    'abr': 'Abr', 'abril': 'Abr',
    'may': 'May', 'mayo': 'May',
    'jun': 'Jun', 'junio': 'Jun',
    'jul': 'Jul', 'julio': 'Jul',
    'ago': 'Ago', 'agosto': 'Ago',
    'sep': 'Sep', 'septiembre': 'Sep', 'setiembre': 'Sep',
    'oct': 'Oct', 'octubre': 'Oct',
    'nov': 'Nov', 'noviembre': 'Nov',
    'dic': 'Dic', 'diciembre': 'Dic',
    // Inglés
    'jan': 'Ene', 'january': 'Ene',
    'apr': 'Abr', 'april': 'Abr',
    'aug': 'Ago', 'august': 'Ago',
    'dec': 'Dic', 'december': 'Dic',
    'october': 'Oct',
    'november': 'Nov',
    'june': 'Jun',
    'july': 'Jul',
    'september': 'Sep',
    'february': 'Feb',
    'march': 'Mar',
  };

  if (mappings[str] !== undefined) {
    return mappings[str];
  }

  // Probar con prefijo de 3 caracteres
  const prefix = str.substring(0, 3);
  if (mappings[prefix] !== undefined) {
    return mappings[prefix];
  }

  // Fallback: capitalizar primera letra del prefijo de 3 letras
  if (str.length >= 3) {
    return str.charAt(0).toUpperCase() + str.substring(1, 3);
  }

  return 'Ene';
}
