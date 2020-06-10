
# Naming Conventions in an NCPI FHIR Data Model

The FHIR specification does not mandate any naming convention or consistency
in resource IDs or resource file names. It is up to the implementers
to choose these standards and follow them.

This document describes a set of naming conventions for resource ids and
file names which are enforced by the NCPI FHIR utility during validation of the
FHIR model. Thus any FHIR model that is being validated using the utility is
expected to follow these naming standards.

## Resource Id

### Semantics

The `id` attribute for a resource in the FHIR model should be
populated with some kind of logical value that describes the semantics of
the resource (e.g. `ResearchParticipant` vs `2349703`).

**NOTE:** This ONLY applies to the files in the FHIR model. Non-conformance
resources (representing real data) loaded into the FHIR server will likely
have an autogenerated alphanumeric ID which may or may not be random.

### Syntax

The `id` value should conform to the regex pattern in the
[FHIR spec](https://www.hl7.org/fhir/datatypes.html#id).

### Casing

All resource `id` values should have the same casing. There does not seem
to be a consistent standard or recommendation for this, but we should pick
one and stick to it.

Based on observations, the FHIR spec seems to use PascalCase for
resource types (e.g. `Patient`, `SearchParameter`) and camelCase
(e.g. `gender`, `birthDate`) for resource attributes.

The Kids First resource `id` values will be lowercased with hyphens between
words (e.g. `age-at-event`, `sequencing-experiment`).  

## Resource File Name

All resource file names should follow the pattern expected by the
[HL7 IG Publisher](https://confluence.hl7.org/display/FHIR/IG+Publisher+Documentation):

**Pattern**

```
<resource type>-<resource id>.json
```

### File Name Delimiter

The file name delimiter will be a hyphen `-`.

**Example StructureDefinition Resource**

```json
{
  "resourceType": "StructureDefinition",
  "id": "participant",
  "url": "https://fhir.ncpi.io/StructureDefinition/participant",
  "name": "participant",
  "status": "draft",
  "fhirVersion": "4.0.0",
  "kind": "resource",
  "abstract": false,
  "type": "Patient",
  "baseDefinition": "https://hl7.org/fhir/StructureDefinition/Patient",
  "derivation": "constraint",
  "differential": {
    "element": [
      {
        "id": "Patient.gender",
        "path": "Patient.gender",
        "min": 1
      },
      {
        "id": "Patient.birthDate",
        "path": "Patient.birthDate",
        "max": "0"
      }
    ]
  }
}
```

**File Name Example**

```
StructureDefinition-participant.json
```

**Example Patient**

```json
{
    "resourceType":"Patient",
    "id": "pt-001",
    "meta": {
        "profile": [
            "https://fhir.ncpi.io/StructureDefinition/participant"
        ]
    },
    "gender": "female",
    "name": [
        {
            "family":"Smith"
        }
    ]
}
```

**File Name Example**

```
Patient-pt-001.json
```

## Specific Rules for StructureDefinitions

The following rules apply to non-Extension type `StructureDefinitions` and
are intended to help Kids First separate the constraints for
Protected Health Information (PHI) from the constraints in base Kids First
profiles.

All `StructureDefinition.id` values will be split into two tokens. The first
token will be a prefix (e.g. `ncpi-`), and the second token will be the name of
the profile.

If a StructureDefinition does not change the underlying meaning of the
FHIR base type it is profiling, then the `id` of the FHIR base resource will be
used as the second token.

- **Example 1**: the NCPI condition profile will have an
  id = ` ncpi-condition` because it is simply extending `Condition` by adding
  the `age-at-event` extension
- **Example 2**: the NCPI phenotype profile will have an
  id = ` ncpi-phenotype` because it is representing a specific kind of
  observation.