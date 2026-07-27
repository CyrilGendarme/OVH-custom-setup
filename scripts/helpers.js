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

export function normalizeIncomingTrackEvent(rawData) {
    const parsed = parseIncomingPayload(rawData);

    if (!parsed || typeof parsed !== "object") {
        return null;
    }

    const nestedPayload =
        parsed.payload && typeof parsed.payload === "object"
            ? parsed.payload
            : parsed.data && typeof parsed.data === "object"
              ? parsed.data
              : parsed.event && typeof parsed.event === "object"
                ? parsed.event
                : parsed;

    const type =
        firstMeaningful(nestedPayload, ["type", "event_type"]) ||
        "track_update";
    if (type && type !== "track_update") {
        return null;
    }

    const artist = firstMeaningful(nestedPayload, ["artist", "artist_name"]);
    const title = firstMeaningful(nestedPayload, [
        "title",
        "track",
        "track_name",
        "song",
    ]);
    const message =
        firstMeaningful(nestedPayload, ["message", "text"]) ||
        (artist && title ? `${artist} - ${title}` : title || artist);

    return {
        ...nestedPayload,
        type,
        artist,
        title,
        message,
        track_id: firstMeaningful(nestedPayload, ["track_id", "id"]),
        rank: firstMeaningful(nestedPayload, ["rank", "position"]),
    };
}

export function firstMeaningful(payload, keys) {
    for (const key of keys) {
        if (isMeaningfulValue(payload[key])) {
            return String(payload[key]).trim();
        }
    }
    return "";
}
