import { lazy } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const WorkflowPanel = lazy(() => import("../components/WorkflowPanel"));

export default function WorkflowRoute() {
  const location = useLocation();
  const navigate = useNavigate();
  const recoverSessionId = location.state?.recoverSessionId;
  return (
    <WorkflowPanel
      recoverSessionId={recoverSessionId}
      // 恢复完成后只清掉 location.state（防止再次进入时重复恢复），用户仍留在 /workflow
      onRecovered={() => navigate("/workflow", { replace: true, state: null })}
    />
  );
}
