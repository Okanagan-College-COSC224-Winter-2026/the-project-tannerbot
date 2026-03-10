import { importStudentsForCourse } from "./api";

  export const importCSV = (id: string | number) => {
    // Prompt the user to select a file
    const input = document.createElement("input");
    input.setAttribute("type", "file");

    // Handle the file selection event
    input.addEventListener("change", async () => {
      const file = input.files?.[0];
      const reader = new FileReader();

      reader.onload = async () => {
        const text = reader.result?.toString();

        if (!text) {
          alert("Please select a file to upload");
          return;
        }

        await importStudentsForCourse(Number(id), text)
          .then((result) => {
            const details: string[] = [];
            if (typeof result?.added_count === "number") {
              details.push(`Added: ${result.added_count}`);
            }
            if (typeof result?.already_enrolled_count === "number") {
              details.push(`Already enrolled: ${result.already_enrolled_count}`);
            }
            if (typeof result?.created_accounts_count === "number") {
              details.push(`New accounts created: ${result.created_accounts_count}`);
            }

            const detailText = details.length > 0 ? `\n${details.join(" | ")}` : "";
            alert((result?.msg || "Students imported successfully") + detailText);
            window.location.reload();
          })
          .catch((error: Error) => {
            alert("Error: " + error.message);
          });
      };

      if (!file) {
        alert("Please select a file to upload");
        return;
      }

      reader.readAsText(file);
    });

    input.click();
  };