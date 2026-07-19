export function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export function randomDelay(base = baseSpeed, randomness = 0.2) {
    const variation = base * randomness;

    return base + (Math.random() * variation * 2 - variation);
}

export function isMeaningfulValue(value) {
    if (value === null || value === undefined) {
        return false;
    }

    const normalized = String(value).trim();
    if (!normalized) {
        return false;
    }

    const lowered = normalized.toLowerCase();
    return lowered !== "none" && lowered !== "null";
}

export function parseIncomingPayload(rawData) {
    if (typeof rawData === "string") {
        try {
            return JSON.parse(rawData);
        } catch (error) {
            return { message: rawData };
        }
    }

    if (rawData && typeof rawData === "object") {
        return rawData;
    }

    return {};
}

export function firstMeaningful(payload, keys) {
    for (const key of keys) {
        if (isMeaningfulValue(payload[key])) {
            return String(payload[key]).trim();
        }
    }
    return "";
}
