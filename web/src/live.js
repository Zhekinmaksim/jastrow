const EXPLORER = "https://explorer-bradbury.genlayer.com";
const POLL_MS = 10000;
const MAX_POLLS = 90;

const els = {
  input: document.getElementById("live-input"),
  connect: document.getElementById("live-connect"),
  submit: document.getElementById("live-submit"),
  status: document.getElementById("live-status"),
  contract: document.getElementById("live-contract"),
  tx: document.getElementById("live-tx"),
  life: document.getElementById("live-life"),
};

let account = "";
let report = null;
let readClient = null;
let writeClient = null;
let sdk = null;

async function ensureSdk() {
  if (sdk) return sdk;
  const [core, chains] = await Promise.all([
    import("genlayer-js"),
    import("genlayer-js/chains"),
  ]);
  sdk = { createClient: core.createClient, testnetBradbury: chains.testnetBradbury };
  return sdk;
}

function embeddedReport() {
  const node = document.getElementById("report-data");
  if (!node) return null;
  try {
    return JSON.parse(node.textContent);
  } catch {
    return null;
  }
}

function short(value) {
  if (!value || value.length < 18) return value || "";
  return value.slice(0, 10) + "..." + value.slice(-6);
}

function setStatus(message, detail) {
  els.status.textContent = "";
  const strong = document.createElement("strong");
  strong.textContent = message;
  els.status.appendChild(strong);
  if (detail) {
    els.status.appendChild(document.createElement("br"));
    els.status.appendChild(document.createTextNode(detail));
  }
}

function contractAddress() {
  return report?.provenance?.contract || "";
}

function populateInputs() {
  els.input.textContent = "";
  const rows = report?.rows || [];
  rows
    .slice()
    .sort((a, b) => a.input_id - b.input_id)
    .forEach((row) => {
      const option = document.createElement("option");
      option.value = String(row.input_id);
      option.textContent = row.label + " (input " + row.input_id + ")";
      els.input.appendChild(option);
    });
}

async function connectWallet() {
  const { createClient, testnetBradbury } = await ensureSdk();
  if (!window.ethereum) {
    setStatus("Wallet not found", "Install MetaMask or another injected wallet.");
    return;
  }
  const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
  account = accounts?.[0] || "";
  if (!account) {
    setStatus("Wallet locked", "No account was returned by the wallet.");
    return;
  }
  writeClient = createClient({
    chain: testnetBradbury,
    account,
    provider: window.ethereum,
  });
  if (!readClient) {
    readClient = createClient({ chain: testnetBradbury });
  }
  await writeClient.connect("testnetBradbury");
  els.connect.textContent = short(account);
  els.submit.disabled = !contractAddress();
  setStatus("Wallet connected", account);
}

async function fetchExplorer(hash) {
  const response = await fetch(EXPLORER + "/api/v1/transactions/" + hash, {
    headers: { accept: "application/json" },
  });
  if (!response.ok) throw new Error("Explorer returned " + response.status);
  return response.json();
}

function receiptState(receipt) {
  const status = String(receipt?.status || receipt?.status_name || "pending").toUpperCase();
  const result = String(receipt?.execution_result || receipt?.txExecutionResultName || "");
  return { status, result };
}

async function poll(hash) {
  for (let i = 0; i < MAX_POLLS; i += 1) {
    try {
      let receipt = null;
      try {
        receipt = await readClient.getTransaction({ hash });
      } catch {
        receipt = await fetchExplorer(hash);
      }
      const state = receiptState(receipt);
      els.life.textContent = state.status + (state.result ? " / " + state.result : "");
      if (["ACCEPTED", "FINALIZED", "UNDETERMINED"].includes(state.status)) {
        setStatus("Transaction " + state.status.toLowerCase(), state.result || "Receipt available.");
        return;
      }
      setStatus("Transaction pending", "Poll " + (i + 1) + " of " + MAX_POLLS + ".");
    } catch (error) {
      setStatus("Waiting for receipt", error.message || String(error));
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
  setStatus("Still pending", "The transaction hash is valid, but no terminal receipt was observed in this browser session.");
}

async function runProbe() {
  if (!writeClient) {
    await connectWallet();
    if (!writeClient) return;
  }
  const address = contractAddress();
  if (!address) {
    setStatus("No contract address", "Embed a chain-receipt report before using the live call.");
    return;
  }
  const inputId = Number(els.input.value);
  els.submit.disabled = true;
  setStatus("Confirm in wallet", "Calling probe(" + report.spec_id + ", " + inputId + ").");
  try {
    const hash = await writeClient.writeContract({
      address,
      functionName: "probe",
      args: [Number(report.spec_id), inputId],
      value: 0n,
    });
    els.tx.innerHTML = "";
    const link = document.createElement("a");
    link.href = EXPLORER + "/transactions/" + hash;
    link.rel = "noreferrer";
    link.target = "_blank";
    link.textContent = short(hash);
    els.tx.appendChild(link);
    els.life.textContent = "submitted";
    setStatus("Transaction submitted", hash);
    await poll(hash);
  } catch (error) {
    setStatus("Transaction failed", error.message || String(error));
    els.life.textContent = "error";
  } finally {
    els.submit.disabled = !contractAddress();
  }
}

function boot() {
  report = embeddedReport();
  populateInputs();
  const address = contractAddress();
  els.contract.textContent = address ? short(address) : "not set";
  if (!address) {
    els.submit.disabled = true;
    setStatus("No deployed contract embedded", "Run receipt_report and embed it before submission.");
  } else {
    setStatus("Ready", "Connect a wallet to submit a probe to " + short(address) + ".");
  }
  els.connect.addEventListener("click", connectWallet);
  els.submit.addEventListener("click", runProbe);
  ensureSdk()
    .then(({ createClient, testnetBradbury }) => {
      readClient = createClient({ chain: testnetBradbury });
    })
    .catch(() => {
      setStatus("SDK load failed", "The static report still works; live calls need genlayer-js.");
    });
}

boot();
