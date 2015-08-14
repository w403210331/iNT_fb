var intScripts = (function ($) {
  function init () {
    $('.results-table').DataTable({
      "columnDefs": [
        { "orderable": false, "targets": -1 }
      ],
      'dom': '',
      'pageLength': 30
    });
    $('.navbar-nav').on('click', '.dropdown-menu', function(e) {
      e.stopPropagation();
    });
    $('.datepicker').on('click', function(e) {
      e.stopPropagation();
    });
    $('.input-daterange').datepicker({
      autoclose: true
    });
    // $('.filter-form').datepicker({
    //   inputs: $('.datepicker').toArray()
    // });
    // $('.datepicker').on('changeDate', function() {
    //   var $datepicker = $(this);
    //   $datepicker.next('input').val(
    //     $datepicker.datepicker('getFormattedDate')
    //   );
    // });
  }

  return {
    init : init
  };
}(jQuery));

intScripts.init();
