project('Grapik Quran',
          version: '0.1.0-alpha.5',
    meson_version: '>= 0.54.0',
  default_options: [ 'warning_level=2',
                   ],
)

dependency('libhandy-1', version: '>= 1.0.0')

i18n = import('i18n')


subdir('data')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
