export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  // Отложенно — некоторые браузеры читают href асинхронно после click().
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
