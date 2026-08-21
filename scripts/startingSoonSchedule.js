export const TARGET_HOUR = 19;
export const TARGET_MINUTE = 30;
export const STARTING_SOON_WINDOW_SECONDS = 5 * 60;

export function hasStartingSoonTarget() {
    return TARGET_HOUR != null && TARGET_MINUTE != null;
}

export function getTargetDate(now = new Date()) {
    const target = new Date(now);

    target.setHours(TARGET_HOUR, TARGET_MINUTE, 0, 0);

    if (target <= now) {
        target.setDate(target.getDate() + 1);
    }

    return target;
}

export function getRemainingSecondsUntilStart(now = new Date()) {
    if (!hasStartingSoonTarget()) {
        return null;
    }

    return Math.floor((getTargetDate(now) - now) / 1000);
}

export function shouldUseStartingSoonBackground(now = new Date()) {
    const remainingSeconds = getRemainingSecondsUntilStart(now);

    return (
        remainingSeconds != null &&
        remainingSeconds > 0 &&
        remainingSeconds <= STARTING_SOON_WINDOW_SECONDS
    );
}
