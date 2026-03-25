import { useMemo } from "react";
import { resolveTripConfig } from "../config/tripConfig";

export function useTripConfig({ tripType, isInternationalReturn = false }) {
    return useMemo(
        () => resolveTripConfig({ tripType, isInternationalReturn }),
        [tripType, isInternationalReturn],
    );
}
