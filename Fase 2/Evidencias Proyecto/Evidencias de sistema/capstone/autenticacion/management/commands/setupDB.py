from django.core.management.base import BaseCommand
from django.db import transaction
from autenticacion.models import (
    Ocupacion,
    Rol, 
    AreaInteres, 
    Institucion, 
    TipoInstitucion, 
    Nivel_educacional,
    Pais, 
    Region, 
    Comuna
)

class Command(BaseCommand):
    help = 'Inicializa la base de datos con datos esenciales: Geografía de Chile (País, Regiones, Comunas), Roles, Áreas e Instituciones de Educación Superior.'

    # --- DATOS GEOGRÁFICOS ---
    CHILE_REGIONES = [
        ('XV', 'Arica y Parinacota'), ('I', 'Tarapacá'), ('II', 'Antofagasta'), 
        ('III', 'Atacama'), ('IV', 'Coquimbo'), ('V', 'Valparaíso'), 
        ('VI', 'O’Higgins'), ('VII', 'Maule'), ('VIII', 'Biobío'), 
        ('IX', 'La Araucanía'), ('XIV', 'Los Ríos'), ('X', 'Los Lagos'),
        ('XI', 'Aysén'), ('XII', 'Magallanes y Antártica Chilena'), 
        ('RM', 'Metropolitana de Santiago'), ('XVI', 'Ñuble')
    ]

    CHILE_COMUNAS = [
        ('Arica', 'XV'), ('Camarones', 'XV'), ('Putre', 'XV'), ('General Lagos', 'XV'),
        ('Iquique', 'I'), ('Alto Hospicio', 'I'), ('Pozo Almonte', 'I'), ('Camiña', 'I'),
        ('Colchane', 'I'), ('Huara', 'I'), ('Pica', 'I'),
        ('Antofagasta', 'II'), ('Mejillones', 'II'), ('Sierra Gorda', 'II'), ('Taltal', 'II'),
        ('Calama', 'II'), ('Ollagüe', 'II'), ('San Pedro de Atacama', 'II'), ('Tocopilla', 'II'),
        ('María Elena', 'II'),
        ('Copiapó', 'III'), ('Caldera', 'III'), ('Tierra Amarilla', 'III'), ('Chañaral', 'III'),
        ('Diego de Almagro', 'III'), ('Vallenar', 'III'), ('Alto del Carmen', 'III'), ('Freirina', 'III'),
        ('Huasco', 'III'),
        ('La Serena', 'IV'), ('Coquimbo', 'IV'), ('Andacollo', 'IV'), ('La Higuera', 'IV'),
        ('Paiguano', 'IV'), ('Vicuña', 'IV'), ('Illapel', 'IV'), ('Canela', 'IV'),
        ('Los Vilos', 'IV'), ('Salamanca', 'IV'), ('Ovalle', 'IV'), ('Combarbalá', 'IV'),
        ('Monte Patria', 'IV'), ('Punitaqui', 'IV'), ('Río Hurtado', 'IV'),
        ('Valparaíso', 'V'), ('Casablanca', 'V'), ('Concón', 'V'), ('Juan Fernández', 'V'),
        ('Puchuncaví', 'V'), ('Quintero', 'V'), ('Viña del Mar', 'V'), ('Isla de Pascua', 'V'),
        ('Los Andes', 'V'), ('Calle Larga', 'V'), ('Rinconada', 'V'), ('San Esteban', 'V'),
        ('La Ligua', 'V'), ('Cabildo', 'V'), ('Papudo', 'V'), ('Petorca', 'V'),
        ('Zapallar', 'V'), ('Quillota', 'V'), ('Calera', 'V'), ('Hijuelas', 'V'),
        ('La Cruz', 'V'), ('Nogales', 'V'), ('San Antonio', 'V'), ('Algarrobo', 'V'),
        ('Cartagena', 'V'), ('El Quisco', 'V'), ('El Tabo', 'V'), ('Santo Domingo', 'V'),
        ('San Felipe', 'V'), ('Catemu', 'V'), ('Llaillay', 'V'), ('Panquehue', 'V'),
        ('Putaendo', 'V'), ('Santa María', 'V'),
        ('Rancagua', 'VI'), ('Codegua', 'VI'), ('Coinco', 'VI'), ('Coltauco', 'VI'),
        ('Doñihue', 'VI'), ('Graneros', 'VI'), ('Las Cabras', 'VI'), ('Machalí', 'VI'),
        ('Malloa', 'VI'), ('Mostazal', 'VI'), ('Olivar', 'VI'), ('Peumo', 'VI'),
        ('Pichidegua', 'VI'), ('Quinta de Tilcoco', 'VI'), ('Rengo', 'VI'), ('Requínoa', 'VI'),
        ('San Vicente', 'VI'), ('Pichilemu', 'VI'), ('La Estrella', 'VI'), ('Litueche', 'VI'),
        ('Marchihue', 'VI'), ('Navidad', 'VI'), ('Paredones', 'VI'), ('San Fernando', 'VI'),
        ('Chépica', 'VI'), ('Chimbarongo', 'VI'), ('Lolol', 'VI'), ('Nancagua', 'VI'),
        ('Palmilla', 'VI'), ('Peralillo', 'VI'), ('Placilla', 'VI'), ('Pumanque', 'VI'),
        ('Santa Cruz', 'VI'),
        ('Talca', 'VII'), ('Constitución', 'VII'), ('Curepto', 'VII'), ('Empedrado', 'VII'),
        ('Maule', 'VII'), ('Pelarco', 'VII'), ('Pencahue', 'VII'), ('Río Claro', 'VII'),
        ('San Clemente', 'VII'), ('San Rafael', 'VII'), ('Cauquenes', 'VII'), ('Chanco', 'VII'),
        ('Pelluhue', 'VII'), ('Curicó', 'VII'), ('Hualañé', 'VII'), ('Licantén', 'VII'),
        ('Molina', 'VII'), ('Rauco', 'VII'), ('Romeral', 'VII'), ('Sagrada Familia', 'VII'),
        ('Teno', 'VII'), ('Vichuquén', 'VII'), ('Linares', 'VII'), ('Colbún', 'VII'),
        ('Longaví', 'VII'), ('Parral', 'VII'), ('Retiro', 'VII'), ('San Javier', 'VII'),
        ('Villa Alegre', 'VII'), ('Yerbas Buenas', 'VII'),
        ('Concepción', 'VIII'), ('Coronel', 'VIII'), ('Chiguayante', 'VIII'), ('Florida', 'VIII'),
        ('Hualpén', 'VIII'), ('Hualqui', 'VIII'), ('Lota', 'VIII'), ('Penco', 'VIII'),
        ('San Pedro de la Paz', 'VIII'), ('Santa Juana', 'VIII'), ('Talcahuano', 'VIII'), ('Tomé', 'VIII'),
        ('Arauco', 'VIII'), ('Cañete', 'VIII'), ('Contulmo', 'VIII'), ('Curanilahue', 'VIII'),
        ('Lebu', 'VIII'), ('Los Álamos', 'VIII'), ('Tirúa', 'VIII'), ('Los Ángeles', 'VIII'),
        ('Antuco', 'VIII'), ('Cabrero', 'VIII'), ('Laja', 'VIII'), ('Mulchén', 'VIII'),
        ('Nacimiento', 'VIII'), ('Negrete', 'VIII'), ('Quilaco', 'VIII'), ('Quilleco', 'VIII'),
        ('San Rosendo', 'VIII'), ('Santa Bárbara', 'VIII'), ('Tucapel', 'VIII'), ('Yumbel', 'VIII'),
        ('Alto Biobío', 'VIII'),
        ('Temuco', 'IX'), ('Carahue', 'IX'), ('Cunco', 'IX'), ('Curarrehue', 'IX'),
        ('Freire', 'IX'), ('Galvarino', 'IX'), ('Gorbea', 'IX'), ('Lautaro', 'IX'),
        ('Loncoche', 'IX'), ('Melipeuco', 'IX'), ('Nueva Imperial', 'IX'), ('Padre Las Casas', 'IX'),
        ('Perquenco', 'IX'), ('Pitrufquén', 'IX'), ('Pucón', 'IX'), ('Saavedra', 'IX'),
        ('Teodoro Schmidt', 'IX'), ('Toltén', 'IX'), ('Vilcún', 'IX'), ('Villarrica', 'IX'),
        ('Angol', 'IX'), ('Collipulli', 'IX'), ('Curacautín', 'IX'), ('Ercilla', 'IX'),
        ('Lonquimay', 'IX'), ('Los Sauces', 'IX'), ('Lumaco', 'IX'), ('Purén', 'IX'),
        ('Renaico', 'IX'), ('Traiguén', 'IX'), ('Victoria', 'IX'),
        ('Valdivia', 'XIV'), ('Corral', 'XIV'), ('Lanco', 'XIV'), ('Los Lagos', 'XIV'),
        ('Máfil', 'XIV'), ('Mariquina', 'XIV'), ('Paillaco', 'XIV'), ('Panguipulli', 'XIV'),
        ('La Unión', 'XIV'), ('Futrono', 'XIV'), ('Lago Ranco', 'XIV'), ('Río Bueno', 'XIV'),
        ('Puerto Montt', 'X'), ('Calbuco', 'X'), ('Cochamó', 'X'), ('Fresia', 'X'),
        ('Frutillar', 'X'), ('Los Muermos', 'X'), ('Llanquihue', 'X'), ('Maullín', 'X'),
        ('Puerto Varas', 'X'), ('Castro', 'X'), ('Ancud', 'X'), ('Chonchi', 'X'),
        ('Curaco de Vélez', 'X'), ('Dalcahue', 'X'), ('Puqueldón', 'X'), ('Queilén', 'X'),
        ('Quellón', 'X'), ('Quemchi', 'X'), ('Quinchao', 'X'), ('Osorno', 'X'),
        ('Puerto Octay', 'X'), ('Purranque', 'X'), ('Puyehue', 'X'), ('Río Negro', 'X'),
        ('San Juan de la Costa', 'X'), ('San Pablo', 'X'), ('Chaitén', 'X'), ('Futaleufú', 'X'),
        ('Hualaihué', 'X'), ('Palena', 'X'),
        ('Coyhaique', 'XI'), ('Lago Verde', 'XI'), ('Aysén', 'XI'), ('Cisnes', 'XI'),
        ('Guaitecas', 'XI'), ('Cochrane', 'XI'), ('O\'Higgins', 'XI'), ('Tortel', 'XI'),
        ('Chile Chico', 'XI'), ('Río Ibáñez', 'XI'),
        ('Punta Arenas', 'XII'), ('Laguna Blanca', 'XII'), ('Río Verde', 'XII'), ('San Gregorio', 'XII'),
        ('Cabo de Hornos', 'XII'), ('Porvenir', 'XII'), ('Primavera', 'XII'), ('Timaukel', 'XII'),
        ('Natales', 'XII'), ('Torres del Paine', 'XII'),
        ('Santiago', 'RM'), ('Cerrillos', 'RM'), ('Cerro Navia', 'RM'), ('Conchalí', 'RM'),
        ('El Bosque', 'RM'), ('Estación Central', 'RM'), ('Huechuraba', 'RM'), ('Independencia', 'RM'),
        ('La Cisterna', 'RM'), ('La Florida', 'RM'), ('La Granja', 'RM'), ('La Pintana', 'RM'),
        ('La Reina', 'RM'), ('Las Condes', 'RM'), ('Lo Barnechea', 'RM'), ('Lo Espejo', 'RM'),
        ('Lo Prado', 'RM'), ('Macul', 'RM'), ('Maipú', 'RM'), ('Ñuñoa', 'RM'),
        ('Pedro Aguirre Cerda', 'RM'), ('Peñalolén', 'RM'), ('Providencia', 'RM'), ('Pudahuel', 'RM'),
        ('Quilicura', 'RM'), ('Quinta Normal', 'RM'), ('Recoleta', 'RM'), ('Renca', 'RM'),
        ('San Joaquín', 'RM'), ('San Miguel', 'RM'), ('San Ramón', 'RM'), ('Vitacura', 'RM'),
        ('Puente Alto', 'RM'), ('Pirque', 'RM'), ('San José de Maipo', 'RM'), ('Colina', 'RM'),
        ('Lampa', 'RM'), ('Tiltil', 'RM'), ('San Bernardo', 'RM'), ('Buin', 'RM'),
        ('Calera de Tango', 'RM'), ('Paine', 'RM'), ('Melipilla', 'RM'), ('Alhué', 'RM'),
        ('Curacaví', 'RM'), ('María Pinto', 'RM'), ('San Pedro', 'RM'), ('Talagante', 'RM'),
        ('El Monte', 'RM'), ('Isla de Maipo', 'RM'), ('Padre Hurtado', 'RM'), ('Peñaflor', 'RM'),
        ('Chillán', 'XVI'), ('Bulnes', 'XVI'), ('Chillán Viejo', 'XVI'), ('El Carmen', 'XVI'),
        ('Pemuco', 'XVI'), ('Pinto', 'XVI'), ('Quillón', 'XVI'), ('San Ignacio', 'XVI'),
        ('Yungay', 'XVI'), ('Cobquecura', 'XVI'), ('Coelemu', 'XVI'), ('Ninhue', 'XVI'),
        ('Portezuelo', 'XVI'), ('Quirihue', 'XVI'), ('Ránquil', 'XVI'), ('Treguaco', 'XVI'),
        ('San Carlos', 'XVI'), ('Coihueco', 'XVI'), ('Ñiquén', 'XVI'), ('San Fabián', 'XVI'),
        ('San Nicolás', 'XVI')
    ]

    # --- DATOS DE INSTITUCIONES ---
    INSTITUCIONES_DATA = [
        {"nombre": "UNIVERSIDAD DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE SANTIAGO DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE VALPARAÍSO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE ANTOFAGASTA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE LA SERENA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DEL BÍO-BÍO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE LA FRONTERA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE MAGALLANES", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE TALCA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE ATACAMA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE TARAPACÁ", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD ARTURO PRAT", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD METROPOLITANA DE CIENCIAS DE LA EDUCACIÓN", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE PLAYA ANCHA DE CIENCIAS DE LA EDUCACIÓN", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE LOS LAGOS", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD TECNOLÓGICA METROPOLITANA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE O'HIGGINS", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE AYSÉN", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "PONTIFICIA UNIVERSIDAD CATÓLICA DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE CONCEPCIÓN", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD TÉCNICA FEDERICO SANTA MARÍA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "PONTIFICIA UNIVERSIDAD CATÓLICA DE VALPARAÍSO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD AUSTRAL DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD CATÓLICA DEL NORTE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD CATÓLICA DEL MAULE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD CATÓLICA DE LA SANTÍSIMA CONCEPCIÓN", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD CATÓLICA DE TEMUCO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD GABRIELA MISTRAL", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD FINIS TERRAE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DIEGO PORTALES", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD CENTRAL DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD BOLIVARIANA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DEL ALBA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD MAYOR", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD ACADEMIA DE HUMANISMO CRISTIANO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD SANTO TOMÁS", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD LA REPÚBLICA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD SEK", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE LAS AMÉRICAS", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD ANDRÉS BELLO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE VIÑA DEL MAR", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD ADOLFO IBÁÑEZ", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD IBEROAMERICANA DE CIENCIAS Y TECNOLOGÍA, UNICIT", "tipo": "Universidad", "estado": "EN_CIERRE"},
        {"nombre": "UNIVERSIDAD DE ARTES, CIENCIAS Y COMUNICACIÓN - UNIACC", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD AUTÓNOMA DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE LOS ANDES", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD ADVENTISTA DE CHILE", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD SAN SEBASTIÁN", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE ARTE Y CIENCIAS SOCIALES ARCIS", "tipo": "Universidad", "estado": "EN_CIERRE"},
        {"nombre": "UNIVERSIDAD CATÓLICA CARDENAL RAÚL SILVA HENRÍQUEZ", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DEL DESARROLLO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD DE ACONCAGUA", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD LOS LEONES", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD BERNARDO O'HIGGINS", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD TECNOLÓGICA DE CHILE INACAP", "tipo": "Universidad", "estado": "EN_CIERRE"},
        {"nombre": "UNIVERSIDAD MIGUEL DE CERVANTES", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "UNIVERSIDAD ALBERTO HURTADO", "tipo": "Universidad", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL IACC", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL AGRARIO ADOLFO MATTHEI", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL AIEP", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL ARCOS", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL CHILENO BRITÁNICO DE CULTURA", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL CICERÓN", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL DE CHILE", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL DEL VALLE CENTRAL", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL DIEGO PORTALES", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL DR. VIRGINIO GÓMEZ G.", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL DUOC UC", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL EATRI", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL ESCUELA DE CINE DE CHILE", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL ESCUELA DE COMERCIO DE SANTIAGO", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL ESCUELA DE CONTADORES AUDITORES DE SANTIAGO", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL ESCUELA DE MARINA MERCANTE PILOTO PARDO", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL ESCUELA MODERNA DE MÚSICA", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL INACAP", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL INSTITUTO DE ESTUDIOS BANCARIOS GUILLERMO SUBERCASEAUX", "tipo": "Instituto Profesional", "estado": "EN_CIERRE"},
        {"nombre": "INSTITUTO PROFESIONAL INSTITUTO INTERNACIONAL DE ARTES CULINARIAS Y SERVICIOS", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL INSTITUTO NACIONAL DEL FÚTBOL", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL IPG", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL LATINOAMERICANO DE COMERCIO EXTERIOR - IPLACEX", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL LIBERTADOR DE LOS ANDES", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL LOS LAGOS", "tipo": "Instituto Profesional", "estado": "EN_CIERRE"},
        {"nombre": "INSTITUTO PROFESIONAL LOS LEONES", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL PROJAZZ", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL PROVIDENCIA", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL SAN SEBASTIÁN", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "INSTITUTO PROFESIONAL SANTO TOMÁS", "tipo": "Instituto Profesional", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA INSTITUTO CENTRAL DE CAPACITACIÓN EDUCACIONAL ICCE", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE ENAC O CENTRO DE FORMACIÓN TÉCNICA DE LOS ESTABLECIMIENTOS NACIONALES DE EDUCACIÓN CÁRITAS-CHILE", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA CENTRO TECNOLÓGICO SUPERIOR  INFOMED", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA INSTITUTO SUPERIOR ALEMÁN DE COMERCIO INSALCO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA JUAN BOHON", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA SANTO TOMÁS", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA LOS LAGOS", "tipo": "Centro de Formación Técnica", "estado": "EN_CIERRE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA CENCO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA PRODATA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA INSTITUTO SUPERIOR DE ESTUDIOS JURÍDICOS CANON", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA IPROSEC", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA SAN AGUSTÍN", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA ALPES", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA INSTITUTO TECNOLÓGICO DE CHILE - I.T.C.", "tipo": "Centro de Formación Técnica", "estado": "EN_CIERRE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA ESCUELA DE COMERCIO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA LAPLACE O C.F.T.  DE ESTUDIOS SUPERIORES Y CAPACITACIÓN PROFESIONAL LAPLACE", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA INACAP", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DEL MEDIO AMBIENTE", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA LOTA - ARAUCO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA CEDUC - UCN", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA ASISTE", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA PROTEC", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA PONTIFICIA UNIVERSIDAD CATÓLICA DE VALPARAÍSO O CFT PUCV", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA TEODORO WICKEL KLUWEN", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA PROFASOC", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA MANPOWER", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA ESCUELA CULINARIA FRANCESA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA ACADEMIA CHILENA DE YOGA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE ARICA Y PARINACOTA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE TARAPACÁ", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE ANTOFAGASTA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE ATACAMA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE COQUIMBO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE VALPARAÍSO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN METROPOLITANA DE SANTIAGO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DEL LIBERTADOR GENERAL BERNARDO O'HIGGINS", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DEL MAULE", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DEL BÍO BIO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE LA ARAUCANÍA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE LOS RÍOS", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE LOS LAGOS", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE AYSÉN DEL GENERAL CARLOS IBÁÑEZ DEL CAMPO", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"},
        {"nombre": "CENTRO DE FORMACIÓN TÉCNICA DE LA REGIÓN DE MAGALLANES Y ANTÁRTICA CHILENA", "tipo": "Centro de Formación Técnica", "estado": "VIGENTE"}
    ]

    # --- MÉTODOS DE EJECUCIÓN ---

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando script de inicialización de DB...'))

        try:
            with transaction.atomic():
                # 1. GEOGRAFÍA (ORDEN IMPORTANTE: País -> Regiones -> Comunas)
                self._create_pais() 
                self._create_regions() 
                self._create_comunas() 
                
                # 2. OTROS DATOS ESENCIALES
                self._create_roles()
                self._create_areas_interes()
                self._create_instituciones() 
                self._create_ocupaciones()

            self.stdout.write(self.style.SUCCESS('✅ ¡Inicialización de DB completada con éxito!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error durante la inicialización de DB. Se abortó la transacción: {e}'))

    # --- FUNCIONES DE CREACIÓN ---
    
    def _create_pais(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Países'))
        # Crear Chile (asumiendo que es el foco del proyecto)
        Pais.objects.get_or_create(nombre="Chile")
        self.stdout.write('  [País] Creado: Chile')

    def _create_regions(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Regiones'))
        for numero, nombre in self.CHILE_REGIONES:
            Region.objects.get_or_create(
                numero=numero, 
                defaults={'nombre': nombre}
            )
        self.stdout.write(f'  [Regiones] Creadas/Actualizadas: {len(self.CHILE_REGIONES)}')

    def _create_comunas(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Comunas'))
        
        # Mapear por el campo 'numero' para acceso rápido a los objetos Region
        regiones_map = {r.numero: r for r in Region.objects.all()}
        nuevas_comunas = 0

        for nombre_comuna, region_numero in self.CHILE_COMUNAS:
            region_obj = regiones_map.get(region_numero)

            if region_obj:
                obj, created = Comuna.objects.get_or_create(
                    nombre=nombre_comuna,
                    defaults={'region': region_obj}
                )
                if created:
                    nuevas_comunas += 1
            else:
                self.stdout.write(self.style.WARNING(f'  [Comuna] Advertencia: Región número "{region_numero}" no encontrada para {nombre_comuna}'))

        self.stdout.write(f'  [Comunas] Nuevas creadas: {nuevas_comunas} de {len(self.CHILE_COMUNAS)} en total.')

    def _create_roles(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Roles'))
        roles_necesarios = ["Estudiante", "Tutor", "Administrador"]
        for nombre_rol in roles_necesarios:
            Rol.objects.get_or_create(nombre=nombre_rol)

    def _create_ocupaciones(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Roles'))
        ocupaciones_necesarios = ["Estudiante", "Trabajador", "Ninguna", "Ambas"]
        for nombre_ocupacion in ocupaciones_necesarios:
            Ocupacion.objects.get_or_create(nombre=nombre_ocupacion)

    def _create_areas_interes(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Áreas de Interés'))
        areas = ["Matemáticas", "Física", "Historia", "Literatura", "Programación", "Química", "Biología", "Arte"]
        for nombre_area in areas:
            AreaInteres.objects.get_or_create(nombre=nombre_area)

    def _create_instituciones(self):
        self.stdout.write(self.style.HTTP_INFO('-> Creando Tipos, Nivel Educacional e Instituciones'))
        
        # 1. Crear tipos de institución y mapearlos
        tipos = ["Universidad", "Instituto Profesional", "Centro de Formación Técnica"]
        tipo_obj = {}
        for t in tipos:
            obj, created = TipoInstitucion.objects.get_or_create(nombre=t)
            tipo_obj[t] = obj

        # 2. Crear nivel educacional
        nivel_nombre = "Educación Superior"
        nivel_obj, created = Nivel_educacional.objects.get_or_create(nombre=nivel_nombre)

        # 3. Crear las instituciones
        nuevas_instituciones = 0
        for inst in self.INSTITUCIONES_DATA:
            obj, created = Institucion.objects.get_or_create(
                nombre=inst["nombre"].strip(),
                defaults={
                    'tipo_institucion': tipo_obj[inst["tipo"]],
                    'estado': inst["estado"],
                    'neducacional': nivel_obj
                }
            )
            if created:
                nuevas_instituciones += 1
        
        self.stdout.write(f'  [Instituciones] Total cargadas/existentes: {len(self.INSTITUCIONES_DATA)}')
        self.stdout.write(f'  [Instituciones] Nuevas creadas: {nuevas_instituciones}')