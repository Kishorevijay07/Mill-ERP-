// Indian states/UTs with their GST state codes, plus small helpers to remember
// the most recently used states (so they float to the top of a picker).

export interface IndiaState {
  code: string;
  name: string;
}

// GST state codes (alphabetical by name).
export const INDIA_STATES: IndiaState[] = [
  { code: "35", name: "Andaman and Nicobar Islands" },
  { code: "37", name: "Andhra Pradesh" },
  { code: "12", name: "Arunachal Pradesh" },
  { code: "18", name: "Assam" },
  { code: "10", name: "Bihar" },
  { code: "04", name: "Chandigarh" },
  { code: "22", name: "Chhattisgarh" },
  { code: "26", name: "Dadra and Nagar Haveli and Daman and Diu" },
  { code: "07", name: "Delhi" },
  { code: "30", name: "Goa" },
  { code: "24", name: "Gujarat" },
  { code: "06", name: "Haryana" },
  { code: "02", name: "Himachal Pradesh" },
  { code: "01", name: "Jammu and Kashmir" },
  { code: "20", name: "Jharkhand" },
  { code: "29", name: "Karnataka" },
  { code: "32", name: "Kerala" },
  { code: "38", name: "Ladakh" },
  { code: "31", name: "Lakshadweep" },
  { code: "23", name: "Madhya Pradesh" },
  { code: "27", name: "Maharashtra" },
  { code: "14", name: "Manipur" },
  { code: "17", name: "Meghalaya" },
  { code: "15", name: "Mizoram" },
  { code: "13", name: "Nagaland" },
  { code: "21", name: "Odisha" },
  { code: "34", name: "Puducherry" },
  { code: "03", name: "Punjab" },
  { code: "08", name: "Rajasthan" },
  { code: "11", name: "Sikkim" },
  { code: "33", name: "Tamil Nadu" },
  { code: "36", name: "Telangana" },
  { code: "16", name: "Tripura" },
  { code: "09", name: "Uttar Pradesh" },
  { code: "05", name: "Uttarakhand" },
  { code: "19", name: "West Bengal" },
  { code: "97", name: "Other Territory" },
];

export function stateByCode(
  code: string | null | undefined,
): IndiaState | undefined {
  if (!code) return undefined;
  return INDIA_STATES.find((s) => s.code === code);
}

const RECENT_KEY = "rmerp_recent_state_codes";
const RECENT_MAX = 6;

export function readRecentStateCodes(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(RECENT_KEY);
    const parsed = raw ? (JSON.parse(raw) as unknown) : [];
    return Array.isArray(parsed) ? (parsed as string[]) : [];
  } catch {
    return [];
  }
}

export function pushRecentStateCode(code: string, current: string[]): string[] {
  const next = [code, ...current.filter((c) => c !== code)].slice(
    0,
    RECENT_MAX,
  );
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    } catch {
      /* ignore storage failures */
    }
  }
  return next;
}

/** States ordered with the most recently used first, then the rest alphabetically. */
export function orderStates(recentCodes: string[]): IndiaState[] {
  const recent = recentCodes
    .map((c) => stateByCode(c))
    .filter((s): s is IndiaState => Boolean(s));
  const recentSet = new Set(recent.map((s) => s.code));
  const rest = INDIA_STATES.filter((s) => !recentSet.has(s.code));
  return [...recent, ...rest];
}
