Feature: Contract scenarios for independent internal Wenmode adapter calls
  Scenario: Definitions do not escape their document
    Given a document defining an ordinary reference and a footnote
    When it is parsed before a document using those labels without definitions
    Then the second tree equals its independent parse
    And the first tree remains unchanged

  Scenario: Later definitions belong to the later document
    Given two documents defining the same labels with different contents
    When both documents are parsed sequentially
    Then each tree contains only its own reference and footnote contents

  Scenario: An upstream failure does not poison the next call
    Given a parser double that fails during one parse
    When the failure is observed and a second document is parsed
    Then the original exception is propagated unchanged
    And the second call uses a new parser and succeeds