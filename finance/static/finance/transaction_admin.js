(function() {
  function byId(id) { return document.getElementById(id); }
  function wrap(fieldName){ return document.querySelector('.form-row.field-' + fieldName) || document.querySelector('#id_' + fieldName)?.closest('.form-row'); }

  function toggleFields() {
    var kind = byId('id_kind');
    if (!kind) return;
    var k = kind.value;
    var rows = {
      source_wallet: wrap('source_wallet'),
      destination_wallet: wrap('destination_wallet'),
      source_account: wrap('source_account'),
      destination_account: wrap('destination_account'),
      destination_deposit: wrap('destination_deposit'),
      exchange_rate: wrap('exchange_rate')
    };
    function show(row, visible){ if(row){ row.style.display = visible ? '' : 'none'; } }

    // Default hide all optional
    show(rows.source_wallet, false);
    show(rows.destination_wallet, false);
    show(rows.source_account, false);
    show(rows.destination_account, false);
    show(rows.destination_deposit, false);
    show(rows.exchange_rate, false);

    // Add/Remove wallet
    if (k === 'add_to_wallet') {
      show(rows.destination_wallet, true);
      return;
    }
    if (k === 'remove_from_wallet') {
      show(rows.source_wallet, true);
      return;
    }

    // Wallet -> Deposit initial
    if (k === 'wallet_to_deposit_initial') {
      show(rows.source_wallet, true);
      show(rows.destination_deposit, true);
      return;
    }

    // Account -> Wallet
    if (k === 'account_to_wallet') {
      show(rows.source_account, true);
      show(rows.destination_wallet, true);
      show(rows.exchange_rate, true); // may be required for non-rial
      return;
    }

    // Wallet -> Account
    if (k === 'wallet_to_account') {
      show(rows.source_wallet, true);
      show(rows.destination_account, true);
      show(rows.exchange_rate, true); // may be required for non-rial
      return;
    }

    // Wallet <-> Wallet or Account <-> Account generic
    if (k === 'wallet_to_wallet') {
      show(rows.source_wallet, true);
      show(rows.destination_wallet, true);
      return;
    }
    if (k === 'account_to_account') {
      show(rows.source_account, true);
      show(rows.destination_account, true);
      return;
    }

    // Profit kinds are system-generated: hide all
  }

  document.addEventListener('DOMContentLoaded', function() {
    var kind = byId('id_kind');
    if (kind) {
      kind.addEventListener('change', toggleFields);
      toggleFields();
    }
  });
})();


