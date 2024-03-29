const ROLE_HTML = 'html';
const ROLE_CSS = 'css';

const socket = io.connect('/');

let current_tab = 'rules';
const comm_tab = document.querySelector('.container >ul li a[href="comm"]');

const sync_btn = document.querySelector('#sync');



/**
 * manage tabs switching
 **********************************************************/
(() => {
  const menus = document.querySelectorAll('.container >ul li');
  const tabs = document.querySelectorAll('.container .pane');

  menus.forEach((menu) => {
    menu.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      menus.forEach((item) => item.classList.remove('active-menu'));
      menu.classList.add('active-menu');
  
      const target = menu.querySelector('a').getAttribute('href');
      current_tab = target;

      menu.querySelector('a').classList.remove('notification');

      tabs.forEach((tab) => {
        tab.classList.remove('visible');
        if (tab.getAttribute('id') === target)
          tab.classList.add('visible');
      });
    });
  });
})();


class Countdown {
  constructor(container, role) {
    this.__el = document.querySelector(container);
    this.__end = parseInt(this.__el.getAttribute('data-end'));
    this.__tid = null;

    this.__role = document.querySelector(role);
    this.__current_role = this.__role.getAttribute('data-role');

    this.__remaining_time_str = '??:??';

    this.__init();
  }

  __init() {
    if (isNaN(this.__end)) {
      this.__remaining_time_str = '??:??';
      this.__el.innerText = this.__remaining_time_str;
      this.__role.innerText = '????';
    } else {
      this.__role.innerText = this.__current_role;
    }

    this.update();
  }

  update() {
    const now = Math.floor(Date.now() / 1000);
    const diff = this.__end - now;
    if (isNaN(diff)) {
      this.__remaining_time_str = '??:??';
      this.__el.innerText = this.__remaining_time_str;
      return;
    }

    if (diff <= 0) {
      this.__remaining_time_str = 'xx:xx';
      this.__el.innerText = this.__remaining_time_str;
    } else {
      const minutes = Math.floor(diff / 60);
      const seconds = diff % 60;
      this.__remaining_time_str = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      this.__el.innerText = this.__remaining_time_str;
      clearTimeout(this.__tid);
      this.__tid = setTimeout(this.update.bind(this), 1000);
    }
  }

  set_end(end) {
    this.__end = end;
    this.__role.innerText = this.__current_role;
    this.update();
  }

  swap_role() {
    this.__role.innerText = '????';
    this.__current_role = ROLE_CSS === this.__current_role ? ROLE_HTML : ROLE_CSS;
  }

  get_remaining_time() {
    return this.__remaining_time_str;
  }
}

class Editor {
  static TAB_SIZE = 4;

  constructor(input) {
    this.__el = document.querySelector(input);
    this.__handling_input();
  }

  clear() {
    this.__el.value = '';
  }

  get_code() {
    return this.__el.value;
  }

  __handling_input() {
    this.__el.addEventListener('keydown', (e) => {
      if (e.keyCode === 9) {
        e.preventDefault();
        e.stopPropagation();
  
        const { selectionStart: start, selectionEnd: end, value } = e.target;
        const is_shift = e.shiftKey;
        const tab_string = ' '.repeat(Editor.TAB_SIZE);
        const is_tab_space = value.substring(start - Editor.TAB_SIZE, start) === tab_string;
  
        if (is_shift && is_tab_space) {
          e.target.value = value.substring(0, start - Editor.TAB_SIZE) + value.substring(start);
          e.target.selectionStart = e.target.selectionEnd = start - Editor.TAB_SIZE;
        } else if (!is_shift) {
          e.target.value = value.substring(0, start) + tab_string + value.substring(end);
          e.target.selectionStart = e.target.selectionEnd = start + Editor.TAB_SIZE;
        }
      } else {
        let cleaned_text = e.target.value;
        e.target.value = cleaned_text;
      }
    });  
  }
}

class ImageReference {
  static MAGNIFIER_SIZE = 100;
  static MAGNIFIER_SCALE = 10;

  constructor(img_src, canvas_ref, magnifier, replica) {
    this.__img_src = document.querySelector(img_src);
    this.__canvas_ref = document.querySelector(canvas_ref);
    this.__magnifier = document.querySelector(magnifier);
    this.__toast_notif = document.querySelector('#toast-notif');
    this.__replica = document.querySelector(replica);

    this.__replica.contentDocument.body.style.margin = '0';
    this.__replica.contentDocument.body.style.padding = '0';
    this.__replica.contentDocument.body.style.width = '100%';
    this.__replica.contentDocument.body.style.height = '100%';

    this.__setup_event_listeners();

    if (this.__img_src.src !== '') {
      this.__setup_canvas();
    }
  }

  __setup_canvas() {
    this.__canvas_ref.width = this.__img_src.width;
    this.__canvas_ref.height = this.__img_src.height;
    this.__canvas_ref.getContext('2d').drawImage(this.__img_src, 0, 0, this.__img_src.width, this.__img_src.height);
  }

  __setup_event_listeners() {
    this.__canvas_ref.addEventListener('mousemove', this.__handle_mouse_move.bind(this));
    this.__canvas_ref.addEventListener('mouseleave', this.__handle_mouse_leave.bind(this));
    this.__img_src.addEventListener('load', () => this.__setup_canvas());

    this.__replica.contentDocument.body.addEventListener('mousedown', this.__handle_show_preview.bind(this));
    this.__replica.contentDocument.body.addEventListener('mouseup', this.__handle_hide_preview.bind(this));
  }

  __handle_show_preview(event) {
    this.__img_src.style.display = 'block';
  }

  __handle_hide_preview(event) {
    this.__img_src.style.display = 'none';
  }

  __handle_mouse_move(event) {
    const x = event.offsetX;
    const y = event.offsetY;
    
    this.__magnifier.style.left = `${x + 15}px`;
    this.__magnifier.style.top = `${y + 15}px`;
    this.__magnifier.style.display = 'block';
    this.__magnifier.style.width = `${ImageReference.MAGNIFIER_SIZE}px`;
    this.__magnifier.style.height = `${ImageReference.MAGNIFIER_SIZE}px`;

    const ctx = this.__magnifier.getContext('2d');
    ctx.clearRect(0, 0, ImageReference.MAGNIFIER_SIZE, ImageReference.MAGNIFIER_SIZE);

    this.__draw_magnifier_area(ctx, x, y);
    this.__display_hex_color(ctx, x, y);
    this.__display_y_position(ctx, y);
  }

  __draw_magnifier_area(ctx, x, y) {
    const scale = ImageReference.MAGNIFIER_SCALE;
    const { width, height } = this.__img_src;

    ctx.drawImage(this.__img_src, x - scale / 2, y - scale / 2, scale, scale, 0, 0, width, height);

    this.__draw_grid(ctx);
    this.__draw_crosshair(ctx);
  }

  __draw_grid(ctx) {
    const scale = ImageReference.MAGNIFIER_SCALE;

    ctx.beginPath();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 1;
    ctx.setLineDash([1, 1]);
    for (let i = 0; i < this.__magnifier.width; i += scale) {
      ctx.moveTo(i, 0);
      ctx.lineTo(i, this.__magnifier.height);
      ctx.moveTo(0, i);
      ctx.lineTo(this.__magnifier.width, i);
    }
    ctx.stroke();
  }


  __draw_crosshair(ctx) {
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
    ctx.moveTo(this.__magnifier.width / 2, 0);
    ctx.lineTo(this.__magnifier.width / 2, this.__magnifier.height);
    ctx.moveTo(0, this.__magnifier.height / 2);
    ctx.lineTo(this.__magnifier.width, this.__magnifier.height / 2);
    ctx.stroke();
  }

  __display_hex_color(ctx, x, y) {
    const pixel = this.__canvas_ref.getContext('2d').getImageData(x, y, 1, 1).data;
    const hex = `#${pixel[0].toString(16).padStart(2, '0')}${pixel[1].toString(16).padStart(2, '0')}${pixel[2].toString(16).padStart(2, '0')}`;
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
    ctx.fillRect(0, 0, this.__magnifier.width, 20);
    ctx.fillStyle = 'white';
    ctx.font = '15px Arial';
    ctx.fillText(hex, 100, 15);
  }

  __display_y_position(ctx, y) {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
    ctx.fillRect(0, this.__magnifier.height - 20, this.__magnifier.width, 20);
    ctx.fillStyle = 'white';
    ctx.font = '15px Arial';
    ctx.fillText(`${y}`, 100, this.__magnifier.height - 5);
  }


  __handle_mouse_leave(event) {
    this.__magnifier.style.display = 'none';
  }

  set_image(base64) {
    this.__img_src.src = `data:image/png;base64,${base64}`;

    this.__img_src.onload = () => this.__setup_canvas();
  }

  change_img_src(src) {
    this.__img_src.src = src;
  }
}

class LeakDashboard {
  constructor(container) {
    this.__el = document.querySelector(container);
  }

  clear() {
    this.__el.innerHTML = '';
  }

  append(time, text) {
    const li = document.createElement('li');
    const span = document.createElement('span');
    span.innerText = time;

    const pre = document.createElement('pre');
    pre.innerText = text;

    li.appendChild(span);
    li.appendChild(pre);

    this.__el.prepend(li);
  }
}

const countdown = new Countdown('#time-remaining', '.title-role');
const editor = new Editor('#text-editor');
const image_reference = new ImageReference('#ref-img', '#canvas-ref', '#magnifier', '#img-replicat');
const replicat = document.querySelector('#img-replicat');
const leak = new LeakDashboard('#leaks');


if (countdown.get_remaining_time() === 'xx:xx') {
  image_reference.change_img_src('/static/break.gif');
} else if (countdown.get_remaining_time() === '??:??') {
  image_reference.change_img_src('/static/logo.png');
}

socket.on('update', (data) => {
  const { role, code } = data;

  if (role === ROLE_HTML)
    replicat.contentDocument.body.innerHTML = code;
  else if (role === ROLE_CSS)
    replicat.contentDocument.head.innerHTML = `<style>${code}</style>`;
});


socket.on('leak', (data) => {
  const { code } = data;

  leak.append(countdown.get_remaining_time(), code);

  if (current_tab !== 'comm')
    comm_tab.classList.add('notification');
});

socket.on('round_start', (data) => {
  const { round, end } = data;

  editor.clear();
  countdown.set_end(+end);
  
  image_reference.set_image(round.image);
  replicat.contentDocument.body.innerHTML = '';
  replicat.contentDocument.head.innerHTML = '';
});

socket.on('round_end', (data) => {
  const { end } = data;

  countdown.swap_role();

  countdown.set_end(+end);
  editor.clear();
  leak.clear();
  replicat.contentDocument.body.innerHTML = '';
  replicat.contentDocument.head.innerHTML = '';

  image_reference.change_img_src('/static/break.gif');
});


document.querySelector('#sync').addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();

  e.target.disabled = true;

  socket.emit('sync', editor.get_code());

  setTimeout(() => {
    e.target.disabled = false;
  }, 3000);
});
