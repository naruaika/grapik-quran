pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'src')
gnome = import('gnome')

gnome.compile_resources('grapik-quran',
  'grapik_quran.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('NAME', meson.project_name())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'grapik-quran.in',
  output: 'grapik-quran',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

grapik_quran_sources = [
  '__init__.py',
  'constants.py',
  'globals.py',
  'main.py',

  # controllers
  'about.py',
  'headerbar.py',
  'menu.py',
  'musshaf.py',
  'navigation.py',
  'tarajem.py',
  'telaawa.py',
  'window.py',

  # models
  'model.py',
  'main.db',

  # helpers
  'animation.py'
]

install_data(grapik_quran_sources, install_dir: moduledir)

install_data('fonts/Amiri-Regular.ttf',
  install_dir: join_paths(get_option('datadir'), 'fonts')
)
