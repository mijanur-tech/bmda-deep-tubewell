import type { AssignmentItem } from "./assignments.api";

export interface AEAssignmentCoverage {
  total: number;
  assigned: number;
  unassigned: number;
  coveragePercentage: number;
}

export function calculateAEAssignmentCoverage(
  tubewellIds: number[],
  assignments: AssignmentItem[]
): AEAssignmentCoverage {
  const authorizedIds = new Set(tubewellIds);

  const assignedIds = new Set(
    assignments
      .filter(
        (assignment) =>
          assignment.ended_at === null &&
          authorizedIds.has(assignment.tubewell_id)
      )
      .map((assignment) => assignment.tubewell_id)
  );

  const total = authorizedIds.size;
  const assigned = assignedIds.size;
  const unassigned = total - assigned;

  const coveragePercentage =
    total === 0
      ? 0
      : Math.round((assigned / total) * 10000) / 100;

  return {
    total,
    assigned,
    unassigned,
    coveragePercentage,
  };
}
