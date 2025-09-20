(function() {
  console.log('Transaction admin JavaScript loaded successfully!');
  console.log('Current URL:', window.location.href);
  console.log('Document ready state:', document.readyState);
  
  // Simple test to see if JavaScript is running
  if (window.location.href.includes('creditincrease')) {
    console.log('CREDIT INCREASE FORM DETECTED!');
    // Add a visible alert to confirm JavaScript is running
    setTimeout(function() {
      console.log('JavaScript is definitely running on credit increase form!');
    }, 1000);
  }
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
    show(rows.source_account, false);
    show(rows.destination_account, false);
    show(rows.destination_deposit, false);
    show(rows.exchange_rate, false);


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
    if (isAjaxInProgress) {
      console.log('AJAX already in progress, skipping filterAccountChoices');
      return;
    }
    
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

    // Set AJAX flag
    isAjaxInProgress = true;

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
      
      // Clear AJAX flag when request completes (success or error)
      if (xhr.readyState === 4) {
        isAjaxInProgress = false;
      }
    };
    xhr.send();
  }

  // Prevent multiple AJAX calls
  var isAjaxInProgress = false;

  function filterSpecializedFormChoices() {
    console.log('filterSpecializedFormChoices called');
    
    if (isAjaxInProgress) {
      console.log('AJAX already in progress, skipping');
      return;
    }
    
    var user = byId('id_user');
    var sourceAccount = byId('id_source_account');
    var destinationAccount = byId('id_destination_account');
    
    console.log('User field:', user);
    console.log('Source account field:', sourceAccount);
    console.log('Destination account field:', destinationAccount);
    
    if (!user) {
      console.log('No user field found');
      return;
    }
    
    var userId = user.value;
    console.log('User ID:', userId);
    
    // Clear current selections
    if (sourceAccount) sourceAccount.innerHTML = '<option value="">---------</option>';
    if (destinationAccount) destinationAccount.innerHTML = '<option value="">---------</option>';
    
    if (!userId) {
      console.log('No user ID selected');
      return;
    }
    
    console.log('Proceeding with AJAX call for user:', userId);
    
    // Determine form type based on URL or page content
    var isCreditIncrease = window.location.href.includes('creditincrease');
    var isWithdrawalRequest = window.location.href.includes('withdrawalrequest');
    var isAccountTransfer = window.location.href.includes('accounttransfer');
    
    // Set AJAX flag
    isAjaxInProgress = true;
    
    // Make AJAX request to get filtered accounts
    var xhr = new XMLHttpRequest();
    var kind = 'credit_increase'; // default
    if (isWithdrawalRequest) kind = 'withdrawal_request';
    else if (isAccountTransfer) kind = 'account_to_account';
    
    xhr.open('GET', '/api/admin/get-user-accounts/?user_id=' + userId + '&kind=' + kind, true);
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        console.log('AJAX response received:', xhr.responseText);
        var data = JSON.parse(xhr.responseText);
        console.log('Parsed data:', data);
        
        // Populate source account choices
        if (data.source_accounts && sourceAccount) {
          console.log('Populating source accounts:', data.source_accounts);
          data.source_accounts.forEach(function(account) {
            var option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name + ' (' + account.account_type + ')';
            sourceAccount.appendChild(option);
          });
        }
        
        // Populate destination account choices
        if (data.destination_accounts && destinationAccount) {
          console.log('Populating destination accounts:', data.destination_accounts);
          data.destination_accounts.forEach(function(account) {
            var option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name + ' (' + account.account_type + ')';
            destinationAccount.appendChild(option);
          });
        }
      } else if (xhr.readyState === 4) {
        console.log('AJAX error:', xhr.status, xhr.responseText);
      }
      
      // Clear AJAX flag when request completes (success or error)
      if (xhr.readyState === 4) {
        isAjaxInProgress = false;
      }
    };
    xhr.send();
  }

  // Prevent multiple initializations
  var isInitialized = false;

  function initTransactionAdmin() {
    if (isInitialized) {
      console.log('Transaction admin already initialized, skipping');
      return;
    }
    
    console.log('Transaction admin JS loaded');
    console.log('Initializing transaction admin...');
    var kind = byId('id_kind');
    var user = byId('id_user');
    
    console.log('Kind field:', kind);
    console.log('User field:', user);
    console.log('User field value:', user ? user.value : 'N/A');
    
    // Test if we can find the destination account field
    var destinationAccount = byId('id_destination_account');
    console.log('Destination account field:', destinationAccount);
    
    // Test if we can find any form elements
    var allSelects = document.querySelectorAll('select');
    console.log('All select elements found:', allSelects.length);
    allSelects.forEach(function(select, index) {
      console.log('Select ' + index + ':', select.id, select.name);
    });
    
    // Check if this is a specialized form (no kind field)
    var isSpecializedForm = !kind && user;
    console.log('Is specialized form:', isSpecializedForm);
    console.log('Kind field exists:', !!kind);
    console.log('User field exists:', !!user);
    
    // Additional checks for specialized forms
    var isCreditIncrease = window.location.href.includes('creditincrease');
    var isWithdrawalRequest = window.location.href.includes('withdrawalrequest');
    console.log('Is credit increase URL:', isCreditIncrease);
    console.log('Is withdrawal request URL:', isWithdrawalRequest);
    
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
      console.log('Adding user change listener');
      user.addEventListener('change', function() {
        console.log('User changed to:', user.value);
        console.log('Is specialized form:', isSpecializedForm);
        if (isSpecializedForm) {
          console.log('Calling filterSpecializedFormChoices');
          filterSpecializedFormChoices();
        } else {
          console.log('Calling filterAccountChoices');
          filterAccountChoices();
        }
      });
    } else {
      console.log('No user field found!');
    }
    
    // Initial filter if form is being edited
    if (kind && user) {
      filterAccountChoices();
    } else if (isSpecializedForm) {
      // For specialized forms, filter based on the form type
      filterSpecializedFormChoices();
    }
    
    // Also try to filter if user is already selected (for specialized forms)
    if (isSpecializedForm && user && user.value) {
      console.log('User already selected, filtering accounts immediately');
      filterSpecializedFormChoices();
    }
    
    // Check if this is an edit form with pre-selected user
    if (isSpecializedForm && user && user.value && user.value !== '') {
      console.log('Edit form detected with user:', user.value);
      setTimeout(function() {
        filterSpecializedFormChoices();
      }, 100);
    }
    
    // Mark as initialized to prevent multiple initializations
    isInitialized = true;
  }

  // Try multiple ways to initialize
  console.log('Setting up initialization...');
  if (document.readyState === 'loading') {
    console.log('Document still loading, adding DOMContentLoaded listener');
    document.addEventListener('DOMContentLoaded', initTransactionAdmin);
  } else {
    console.log('Document already loaded, running init immediately');
    initTransactionAdmin();
  }
  
  // Also try after a short delay
  console.log('Setting up 500ms delay initialization');
  setTimeout(initTransactionAdmin, 500);
  
  // Try again after a longer delay to ensure form is fully loaded
  console.log('Setting up 1000ms delay initialization');
  setTimeout(function() {
    console.log('Delayed initialization attempt');
    initTransactionAdmin();
  }, 1000);
})();


