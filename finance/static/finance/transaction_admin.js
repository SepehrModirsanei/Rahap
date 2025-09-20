(function() {
  function byId(id) { return document.getElementById(id); }
  function wrap(fieldName){ 
    var row = document.querySelector('.form-row.field-' + fieldName);
    if (!row) {
      var field = document.querySelector('#id_' + fieldName);
      if (field) {
        row = field.closest('.form-row');
      }
    }
    if (!row) {
      // Try alternative selectors
      row = document.querySelector('tr.field-' + fieldName);
    }
    return row;
  }

  function toggleFields() {
    var kind = byId('id_kind');
    if (!kind) return;
    var k = kind.value;
    console.log('Toggling fields for kind:', k);
    var rows = {
      source_wallet: wrap('source_wallet'),
      destination_wallet: wrap('destination_wallet'),
      source_account: wrap('source_account'),
      destination_account: wrap('destination_account'),
      destination_deposit: wrap('destination_deposit'),
      exchange_rate: wrap('exchange_rate')
    };
    console.log('Found rows:', rows);
    console.log('Source account row:', rows.source_account);
    console.log('Destination account row:', rows.destination_account);
    function show(row, visible){ 
      if(row){ 
        row.style.display = visible ? '' : 'none'; 
        console.log('Setting row display:', row.className, visible ? 'visible' : 'hidden');
      } 
    }

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

    // Credit Increase
    if (k === 'credit_increase') {
      show(rows.destination_account, true);
      show(rows.source_account, false);
      return;
    }

    // Withdrawal Request
    if (k === 'withdrawal_request') {
      show(rows.source_account, true);
      show(rows.destination_account, false);
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
      show(rows.exchange_rate, true);
      return;
    }

    // Account to Deposit Initial
    if (k === 'account_to_deposit_initial') {
      show(rows.source_account, true);
      show(rows.destination_deposit, true);
      return;
    }

    // Profit kinds are system-generated: hide all
  }

  function filterAccountChoices() {
    var kind = byId('id_kind');
    var user = byId('id_user');
    var sourceAccount = byId('id_source_account');
    var destinationAccount = byId('id_destination_account');
    
    if (!kind || !user || !sourceAccount || !destinationAccount) return;
    
    var kindValue = kind.value;
    var userId = user.value;
    
    // Clear current selections
    sourceAccount.innerHTML = '<option value="">---------</option>';
    destinationAccount.innerHTML = '<option value="">---------</option>';
    
    if (!userId) return;
    
    // Make AJAX request to get filtered accounts
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/admin/get-user-accounts/?user_id=' + userId + '&kind=' + kindValue, true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        var data = JSON.parse(xhr.responseText);
        
        // Populate source account choices
        if (data.source_accounts) {
          data.source_accounts.forEach(function(account) {
            var option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name + ' (' + account.account_type + ')';
            sourceAccount.appendChild(option);
          });
        }
        
        // Populate destination account choices
        if (data.destination_accounts) {
          data.destination_accounts.forEach(function(account) {
            var option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name + ' (' + account.account_type + ')';
            destinationAccount.appendChild(option);
          });
        }
      }
    };
    xhr.send();
  }

  function initTransactionAdmin() {
    console.log('Transaction admin JS loaded');
    var kind = byId('id_kind');
    var user = byId('id_user');
    
    console.log('Kind field:', kind);
    console.log('User field:', user);
    
    if (kind) {
      kind.addEventListener('change', function() {
        console.log('Kind changed to:', kind.value);
        toggleFields();
        filterAccountChoices();
      });
      // Run toggleFields immediately
      setTimeout(toggleFields, 100);
    }
    
    if (user) {
      user.addEventListener('change', function() {
        console.log('User changed to:', user.value);
        filterAccountChoices();
      });
    }
    
    // Initial filter if form is being edited
    if (kind && user) {
      filterAccountChoices();
    }
  }

  // Try multiple ways to initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTransactionAdmin);
  } else {
    initTransactionAdmin();
  }
  
  // Also try after a short delay
  setTimeout(initTransactionAdmin, 500);
})();


