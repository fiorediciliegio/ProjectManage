import React from "react";
import FileManager from "../components/FileManager.jsx";
import CommonPage from "../components/CommonPage.jsx";
import useProjectParams from "../hooks/useProjectParams.js";

export default function DocumentPage() {
  const { projectName, projectId } = useProjectParams();

  return (
    <CommonPage pageName={"文档"} projectId={projectId} projectName={projectName}>
      <FileManager projectId={projectId} />
    </CommonPage>
  );
}

