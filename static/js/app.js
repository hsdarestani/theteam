(function(){
  const menuButton=document.querySelector('[data-menu]');
  const sidebar=document.getElementById('sidebar');
  if(menuButton&&sidebar){
    menuButton.addEventListener('click',()=>sidebar.classList.toggle('open'));
    document.addEventListener('click',event=>{
      if(window.innerWidth<=860&&!sidebar.contains(event.target)&&!menuButton.contains(event.target)){
        sidebar.classList.remove('open');
      }
    });
  }

  const updateGroupAverage=group=>{
    if(!group)return;
    const inputs=[...document.querySelectorAll(`input[type="range"][data-rating-group="${group}"]`)];
    const output=document.querySelector(`[data-group-average="${group}"]`);
    if(!inputs.length||!output)return;
    const average=inputs.reduce((sum,input)=>sum+Number(input.value),0)/inputs.length;
    output.textContent=average.toFixed(1).replace('.',',');
  };

  document.querySelectorAll('input[type="range"]').forEach(input=>{
    const output=document.querySelector(`[data-output-for="${input.id}"]`);
    const sync=()=>{
      if(output)output.textContent=input.value;
      updateGroupAverage(input.dataset.ratingGroup);
    };
    sync();
    input.addEventListener('input',sync);
  });

  document.querySelectorAll('[data-set-all]').forEach(button=>{
    button.addEventListener('click',()=>{
      const value=button.dataset.setAll||'7';
      document.querySelectorAll('[data-detailed-evaluation] input[type="range"]').forEach(input=>{
        input.value=value;
        input.dispatchEvent(new Event('input',{bubbles:true}));
      });
    });
  });

  document.querySelectorAll('details[data-rating-details]').forEach(details=>{
    details.addEventListener('toggle',()=>{
      if(!details.open||window.innerWidth>860)return;
      document.querySelectorAll('details[data-rating-details][open]').forEach(other=>{
        if(other!==details)other.removeAttribute('open');
      });
    });
  });

  const csrf=()=>{
    const item=document.cookie.split('; ').find(row=>row.startsWith('csrftoken='));
    return item?decodeURIComponent(item.split('=')[1]):'';
  };

  document.querySelectorAll('[data-attendance]').forEach(group=>{
    group.querySelectorAll('button').forEach(button=>button.addEventListener('click',async()=>{
      const status=document.querySelector('[data-save-status]');
      if(status){
        status.textContent='Wird gespeichert …';
        status.className='save-status saving';
      }
      const body=new URLSearchParams({
        action:'attendance',
        attendance_id:group.dataset.id,
        status:button.dataset.value
      });
      try{
        const response=await fetch(group.dataset.url,{
          method:'POST',
          headers:{'X-CSRFToken':csrf(),'X-Requested-With':'XMLHttpRequest'},
          body
        });
        if(!response.ok)throw new Error();
        group.querySelectorAll('button').forEach(item=>item.classList.remove('active'));
        button.classList.add('active');
        if(status){
          status.textContent='Gespeichert';
          status.className='save-status saved';
          setTimeout(()=>{
            status.textContent='Änderungen werden sofort gespeichert';
            status.className='save-status';
          },1600);
        }
      }catch(error){
        if(status){
          status.textContent='Speichern fehlgeschlagen';
          status.className='save-status saving';
        }
      }
    }));
  });

  setTimeout(()=>document.querySelectorAll('.message').forEach(item=>item.remove()),4000);
})();