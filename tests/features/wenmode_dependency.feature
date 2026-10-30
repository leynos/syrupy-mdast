Feature: Python-only Wenmode dependency
  Scenario Outline: The reviewed parser works in isolation
    Given a fresh <mode> installation from the prepared local wheelhouse
    And JavaScript execution and network access are denied
    When the reviewed GitHub parser parses the smoke documents
    Then Wenmode version 0.15.2 is imported from that environment
    And the expected root and child semantics are returned

    Examples:
      | mode     |
      | wheel    |
      | editable |

  Scenario: A missing offline dependency fails visibly
    Given a local wheelhouse without Wenmode and an empty installer cache
    When a fresh wheel installation is attempted offline
    Then installation fails because Wenmode cannot be resolved

  Scenario: A forbidden wheel asset is rejected
    Given a synthetic wheel containing a nested TypeScript file
    When the Python-only archive contract is checked
    Then the forbidden asset is identified
