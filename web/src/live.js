const GENLAYER_EXPLORER = "https://explorer-bradbury.genlayer.com";
const WALLET_EXPLORER = "https://zksync-os-testnet-genlayer.explorer.zksync.dev";
const POLL_MS = 10000;
const MAX_POLLS = 90;
const TX_RE = /0x[a-fA-F0-9]{64}/;

const els = {
  input: document.getElementById("live-input"),
  inputButton: document.getElementById("live-input-button"),
  inputMenu: document.getElementById("live-input-menu"),
  connect: document.getElementById("live-connect"),
  submit: document.getElementById("live-submit"),
  status: document.getElementById("live-status"),
  contract: document.getElementById("live-contract"),
  tx: document.getElementById("live-tx"),
  walletTx: document.getElementById("live-wallet-tx"),
  walletTxInput: document.getElementById("wallet-tx-input"),
  walletTxSave: document.getElementById("wallet-tx-save"),
  life: document.getElementById("live-life"),
};

let account = "";
let report = null;
let readClient = null;
let writeClient = null;
let sdk = null;
let walletProvider = null;

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

function hashFromText(value) {
  const match = String(value || "").match(TX_RE);
  return match ? match[0] : "";
}

function setTxLink(node, baseUrl, hash) {
  const cleanHash = hashFromText(hash);
  node.innerHTML = "";
  if (!cleanHash) {
    node.textContent = "none";
    return "";
  }
  const link = document.createElement("a");
  link.href = baseUrl.replace(/\/$/, "") + "/tx/" + cleanHash;
  link.rel = "noreferrer";
  link.target = "_blank";
  link.textContent = short(cleanHash);
  node.appendChild(link);
  return cleanHash;
}

function setGenlayerTx(hash) {
  return setTxLink(els.tx, GENLAYER_EXPLORER, hash);
}

function setWalletTx(hash) {
  const cleanHash = setTxLink(els.walletTx, WALLET_EXPLORER, hash);
  if (cleanHash) {
    localStorage.setItem("jastrow:last-wallet-tx", cleanHash);
    if (els.walletTxInput) els.walletTxInput.value = cleanHash;
  }
  return cleanHash;
}

function contractAddress() {
  return report?.provenance?.contract || report?.live_contract || "";
}

function injectedProvider() {
  const eth = window.ethereum;
  if (!eth) return null;
  const providers = Array.isArray(eth.providers) ? eth.providers : [eth];
  return (
    providers.find((provider) => provider.isRabby) ||
    providers.find((provider) => provider.isMetaMask) ||
    providers[0]
  );
}

function providerWithWalletTxCapture(provider) {
  if (!provider || provider.__jastrowWalletCapture) return provider;
  const wrapped = Object.create(provider);
  Object.defineProperty(wrapped, "__jastrowWalletCapture", { value: true });
  wrapped.request = async (args) => {
    const result = await provider.request(args);
    if (args?.method === "eth_sendTransaction") {
      const walletHash = hashFromText(result);
      if (walletHash) {
        setWalletTx(walletHash);
        setStatus("Wallet transaction sent", walletHash);
      }
    }
    return result;
  };
  return wrapped;
}

function markWalletConnected(address) {
  account = address || "";
  if (!account) return;
  els.connect.textContent = short(account);
  els.connect.title = account;
  els.connect.classList.add("is-connected");
  els.submit.disabled = !contractAddress();
  setStatus("Wallet connected", account);
}

function markWalletDisconnected(message = "Connect a wallet to submit a probe.") {
  account = "";
  writeClient = null;
  els.connect.textContent = "Connect wallet";
  els.connect.removeAttribute("title");
  els.connect.classList.remove("is-connected");
  els.submit.disabled = true;
  setStatus("Wallet disconnected", message);
}

function populateInputs() {
  els.input.textContent = "";
  els.inputMenu.textContent = "";
  const rows = report?.rows || [];
  rows
    .slice()
    .sort((a, b) => a.input_id - b.input_id)
    .forEach((row) => {
      const value = String(row.input_id);
      const label = row.label + " (input " + row.input_id + ")";
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      els.input.appendChild(option);

      const item = document.createElement("button");
      item.type = "button";
      item.className = "picker-option";
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", "false");
      item.dataset.value = value;

      const name = document.createElement("span");
      name.textContent = row.label;
      const id = document.createElement("span");
      id.className = "option-id";
      id.textContent = "input " + row.input_id;
      item.append(name, id);
      item.addEventListener("click", () => selectInput(value));
      els.inputMenu.appendChild(item);
    });
  if (els.input.options.length) {
    selectInput(els.input.options[0].value, false);
  }
}

function selectInput(value, close = true) {
  els.input.value = String(value);
  const selected = els.input.options[els.input.selectedIndex];
  els.inputButton.textContent = selected ? selected.textContent : "Select input";
  [...els.inputMenu.querySelectorAll(".picker-option")].forEach((item) => {
    item.setAttribute("aria-selected", item.dataset.value === String(value) ? "true" : "false");
  });
  if (close) closeInputMenu();
}

function openInputMenu() {
  els.inputMenu.hidden = false;
  els.inputButton.setAttribute("aria-expanded", "true");
  const selected = els.inputMenu.querySelector('[aria-selected="true"]');
  if (selected) selected.scrollIntoView({ block: "nearest" });
}

function closeInputMenu() {
  els.inputMenu.hidden = true;
  els.inputButton.setAttribute("aria-expanded", "false");
}

function toggleInputMenu() {
  if (els.inputMenu.hidden) openInputMenu();
  else closeInputMenu();
}

async function connectWallet() {
  const { createClient, testnetBradbury } = await ensureSdk();
  walletProvider = injectedProvider();
  if (!walletProvider) {
    setStatus("Wallet not found", "Install MetaMask or another injected wallet.");
    return;
  }
  const accounts = await walletProvider.request({ method: "eth_requestAccounts" });
  account = accounts?.[0] || "";
  if (!account) {
    setStatus("Wallet locked", "No account was returned by the wallet.");
    return;
  }
  markWalletConnected(account);
  writeClient = createClient({
    chain: testnetBradbury,
    account,
    provider: providerWithWalletTxCapture(walletProvider),
  });
  if (!readClient) {
    readClient = createClient({ chain: testnetBradbury });
  }
  try {
    await writeClient.connect("testnetBradbury");
  } catch (error) {
    setStatus(
      "Wallet connected",
      "Account " + short(account) + ". Network handshake can finish when the transaction is submitted."
    );
  }
}

async function syncExistingWallet() {
  const { createClient, testnetBradbury } = await ensureSdk();
  walletProvider = injectedProvider();
  if (!walletProvider) return;
  const accounts = await walletProvider.request({ method: "eth_accounts" });
  const current = accounts?.[0] || "";
  if (!current) return;
  markWalletConnected(current);
  writeClient = createClient({
    chain: testnetBradbury,
    account: current,
    provider: providerWithWalletTxCapture(walletProvider),
  });
}

async function fetchExplorer(hash) {
  const response = await fetch(GENLAYER_EXPLORER + "/api/v1/transactions/" + hash, {
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
    setGenlayerTx(hash);
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
  els.walletTxSave.addEventListener("click", () => {
    const walletHash = setWalletTx(els.walletTxInput.value);
    if (walletHash) {
      setStatus("Wallet transaction linked", walletHash);
    } else {
      setStatus("No wallet tx found", "Paste a 0x transaction hash or a full explorer URL.");
    }
  });
  const savedWalletTx = localStorage.getItem("jastrow:last-wallet-tx");
  if (savedWalletTx) setWalletTx(savedWalletTx);
  els.inputButton.addEventListener("click", toggleInputMenu);
  els.inputButton.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeInputMenu();
      return;
    }
    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openInputMenu();
    }
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest("#live-picker")) closeInputMenu();
  });
  ensureSdk()
    .then(({ createClient, testnetBradbury }) => {
      readClient = createClient({ chain: testnetBradbury });
      return syncExistingWallet();
    })
    .catch(() => {
      setStatus("SDK load failed", "The static report still works; live calls need genlayer-js.");
    });
  const provider = injectedProvider();
  if (provider?.on) {
    provider.on("accountsChanged", (accounts) => {
      const next = accounts?.[0] || "";
      if (next) {
        markWalletConnected(next);
        writeClient = null;
      } else {
        markWalletDisconnected();
      }
    });
  }
}

boot();
