Feature: Public Markdown snapshot extension defers serialisation
  Scenario: A direct call defers serialisation to the planned serializer
    Given the public Markdown snapshot extension
    When a caller serialises a valid Markdown document directly
    Then the extension refuses with the planned roadmap task

  Scenario: A registered Syrupy assertion is refused before serialisation
    Given a Syrupy snapshot assertion using the public extension
    When that assertion compares a valid Markdown document
    Then the comparison does not match
    And Syrupy reports the rejected property control
    And the registered extension is the public type