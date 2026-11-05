import ApprovalPageLegacy from "./ApprovalPageLegacy";
import SAEApprovalWorkspace from "./SAEApprovalWorkspace";

interface ApprovalPageProps {
  role: "supervisor" | "assistant_engineer";
  inline?: boolean;
}

export default function ApprovalPage(props: ApprovalPageProps) {
  if (props.role === "supervisor") {
    return <SAEApprovalWorkspace inline={props.inline} />;
  }

  return <ApprovalPageLegacy {...props} />;
}
