// Synthetic fixture: one goal = process the fixture request.
// Trigger = FixtureCommand. Entry = fixture pending. Outcome = fixture done.
// Actor = fixture client. No OSAGO business knowledge is asserted.
// Synthetic technical main path: accuracy >= 7; alternative path: accuracy < 7.
record FixtureCommand();
class FixtureHandler {
    // Synthetic technical threshold, not an OSAGO business rule.
    public int Handle(FixtureCommand command, int accuracy) {
        if (accuracy < 7) return 0;
        return 1;
    }
}
// Registration: FixtureCommand -> FixtureHandler.Handle
