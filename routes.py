from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app
from database import db_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@app.route('/')
def role_selection():
    """Role selection page"""
    return render_template('role_selection.html')

@app.route('/dashboard')
@app.route('/dashboard/medico')
def dashboard():
    """Main dashboard with medical system overview"""
    try:
        # Get dashboard statistics
        stats = {}
        
        # Total patients
        total_patients_query = "SELECT COUNT(*) as count FROM Paciente"
        result = db_manager.execute_single_query(total_patients_query)
        stats['total_patients'] = result['count'] if result else 0
        
        # Total clinical histories
        total_histories_query = "SELECT COUNT(*) as count FROM HistoriaClinica"
        result = db_manager.execute_single_query(total_histories_query)
        stats['total_histories'] = result['count'] if result else 0
        
        # Total admissions
        total_admissions_query = "SELECT COUNT(*) as count FROM AdmisionPaciente"
        result = db_manager.execute_single_query(total_admissions_query)
        stats['total_admissions'] = result['count'] if result else 0
        
        # Total professionals
        total_professionals_query = "SELECT COUNT(*) as count FROM ProfesionalSalud"
        result = db_manager.execute_single_query(total_professionals_query)
        stats['total_professionals'] = result['count'] if result else 0
        
        # Recent admissions (last 10)
        recent_admissions_query = """
        SELECT ap.id_admision, ap.fecha_admision, ap.motivo_ingreso, ap.via_ingreso,
               p.nombres, p.apellidos, p.documento_identidad,
               ps.nombres as prof_nombres, ps.apellidos as prof_apellidos
        FROM AdmisionPaciente ap
        LEFT JOIN Paciente p ON ap.id_paciente = p.id_paciente
        LEFT JOIN ProfesionalSalud ps ON ap.id_admisionista = ps.id_profesional
        ORDER BY ap.fecha_admision DESC
        LIMIT 10
        """
        recent_admissions = db_manager.execute_query(recent_admissions_query)
        
        # Recent clinical evaluations
        recent_evaluations_query = """
        SELECT ec.id_evaluacion, ec.fecha_resultado, ec.instrumento_utilizado, 
               ec.resultado_parametro, ec.resultado_valor,
               p.nombres, p.apellidos, p.documento_identidad
        FROM EvaluacionClinica ec
        LEFT JOIN HistoriaClinica hc ON ec.id_historia_clinica = hc.id_historia_clinica
        LEFT JOIN Paciente p ON hc.id_paciente = p.id_paciente
        ORDER BY ec.fecha_resultado DESC
        LIMIT 10
        """
        recent_evaluations = db_manager.execute_query(recent_evaluations_query)
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_admissions=recent_admissions,
                             recent_evaluations=recent_evaluations)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', stats={}, recent_admissions=[], recent_evaluations=[])

@app.route('/patients')
def patients():
    """Patient list with search functionality"""
    try:
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        # Base query for patients
        base_query = """
        SELECT p.id_paciente, p.nombres, p.apellidos, p.documento_identidad,
               p.fecha_nacimiento, p.edad, p.sexo, p.ocupacion, p.correo,
               p.municipio_residencia, p.zona_residencia
        FROM Paciente p
        """
        
        # Add search conditions if search term provided
        if search:
            search_query = base_query + """
            WHERE p.nombres LIKE %s 
               OR p.apellidos LIKE %s 
               OR p.documento_identidad LIKE %s
               OR CONCAT(p.nombres, ' ', p.apellidos) LIKE %s
            ORDER BY p.nombres, p.apellidos
            LIMIT %s OFFSET %s
            """
            search_term = f'%{search}%'
            patients_list = db_manager.execute_query(search_query, 
                                                   (search_term, search_term, search_term, search_term, per_page, offset))
            
            # Count total for pagination
            count_query = """
            SELECT COUNT(*) as count FROM Paciente p
            WHERE p.nombres LIKE %s 
               OR p.apellidos LIKE %s 
               OR p.documento_identidad LIKE %s
               OR CONCAT(p.nombres, ' ', p.apellidos) LIKE %s
            """
            count_result = db_manager.execute_single_query(count_query, 
                                                         (search_term, search_term, search_term, search_term))
        else:
            # Get all patients with pagination
            patients_query = base_query + """
            ORDER BY p.nombres, p.apellidos
            LIMIT %s OFFSET %s
            """
            patients_list = db_manager.execute_query(patients_query, (per_page, offset))
            
            # Count total for pagination
            count_query = "SELECT COUNT(*) as count FROM Paciente"
            count_result = db_manager.execute_single_query(count_query)
        
        total_count = count_result['count'] if count_result else 0
        total_pages = (total_count + per_page - 1) // per_page
        
        return render_template('patients.html', 
                             patients=patients_list, 
                             search=search,
                             page=page,
                             total_pages=total_pages,
                             total_count=total_count)
    
    except Exception as e:
        logger.error(f"Patients page error: {e}")
        flash(f'Error loading patients: {str(e)}', 'error')
        return render_template('patients.html', patients=[], search='', page=1, total_pages=1, total_count=0)

@app.route('/clinical_history/<int:patient_id>')
def clinical_history(patient_id):
    """Clinical history details for a specific patient"""
    try:
        # Get patient information
        patient_query = """
        SELECT * FROM Paciente WHERE id_paciente = %s
        """
        patient = db_manager.execute_single_query(patient_query, (patient_id,))
        
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        # Get clinical histories for this patient
        histories_query = """
        SELECT hc.*, ap.fecha_admision, ap.motivo_ingreso, ap.via_ingreso,
               pi.nombres as prof_ingreso_nombres, pi.apellidos as prof_ingreso_apellidos,
               pe.nombres as prof_egreso_nombres, pe.apellidos as prof_egreso_apellidos,
               inst.nombre as institucion_nombre
        FROM HistoriaClinica hc
        LEFT JOIN AdmisionPaciente ap ON hc.id_admision = ap.id_admision
        LEFT JOIN ProfesionalSalud pi ON hc.id_profesional_ingreso = pi.id_profesional
        LEFT JOIN ProfesionalSalud pe ON hc.id_profesional_egreso = pe.id_profesional
        LEFT JOIN InstitucionSalud inst ON hc.id_institucion = inst.id_institucion
        WHERE hc.id_paciente = %s
        ORDER BY ap.fecha_admision DESC
        """
        histories = db_manager.execute_query(histories_query, (patient_id,))
        
        # Get antecedents for this patient
        antecedents_query = """
        SELECT a.* FROM Antecedentes a
        INNER JOIN HistoriaClinica hc ON a.id_historia_clinica = hc.id_historia_clinica
        WHERE hc.id_paciente = %s
        """
        antecedents = db_manager.execute_query(antecedents_query, (patient_id,))
        
        # Get diagnoses for this patient
        diagnoses_query = """
        SELECT d.* FROM Diagnostico d
        INNER JOIN HistoriaClinica hc ON d.id_historia_clinica = hc.id_historia_clinica
        WHERE hc.id_paciente = %s
        ORDER BY hc.id_historia_clinica DESC
        """
        diagnoses = db_manager.execute_query(diagnoses_query, (patient_id,))
        
        # Get treatments for this patient
        treatments_query = """
        SELECT t.* FROM Tratamiento t
        INNER JOIN HistoriaClinica hc ON t.id_historia_clinica = hc.id_historia_clinica
        WHERE hc.id_paciente = %s
        ORDER BY hc.id_historia_clinica DESC
        """
        treatments = db_manager.execute_query(treatments_query, (patient_id,))
        
        # Get incapacities for this patient
        incapacities_query = """
        SELECT i.* FROM Incapacidad i
        INNER JOIN HistoriaClinica hc ON i.id_historia_clinica = hc.id_historia_clinica
        WHERE hc.id_paciente = %s
        ORDER BY hc.id_historia_clinica DESC
        """
        incapacities = db_manager.execute_query(incapacities_query, (patient_id,))
        
        return render_template('clinical_history.html',
                             patient=patient,
                             histories=histories,
                             antecedents=antecedents,
                             diagnoses=diagnoses,
                             treatments=treatments,
                             incapacities=incapacities)
    
    except Exception as e:
        logger.error(f"Clinical history error: {e}")
        flash(f'Error loading clinical history: {str(e)}', 'error')
        return redirect(url_for('patients'))

@app.route('/exams')
def exams():
    """Exams and results page"""
    try:
        search = request.args.get('search', '')
        patient_id = request.args.get('patient_id', '')
        
        # Base query for clinical evaluations
        base_query = """
        SELECT ec.*, hc.id_historia_clinica,
               p.nombres, p.apellidos, p.documento_identidad,
               ap.fecha_admision, ap.motivo_ingreso
        FROM EvaluacionClinica ec
        INNER JOIN HistoriaClinica hc ON ec.id_historia_clinica = hc.id_historia_clinica
        INNER JOIN Paciente p ON hc.id_paciente = p.id_paciente
        LEFT JOIN AdmisionPaciente ap ON hc.id_admision = ap.id_admision
        """
        
        conditions = []
        params = []
        
        # Add search conditions
        if search:
            conditions.append("""
            (p.nombres LIKE %s OR p.apellidos LIKE %s OR p.documento_identidad LIKE %s
             OR ec.instrumento_utilizado LIKE %s OR ec.resultado_parametro LIKE %s)
            """)
            search_term = f'%{search}%'
            params.extend([search_term] * 5)
        
        if patient_id:
            conditions.append("p.id_paciente = %s")
            params.append(patient_id)
        
        # Build final query
        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            query = base_query
        
        query += " ORDER BY ec.fecha_resultado DESC LIMIT 100"
        
        evaluations = db_manager.execute_query(query, params)
        
        # Get patients for filter dropdown
        patients_query = """
        SELECT DISTINCT p.id_paciente, p.nombres, p.apellidos, p.documento_identidad
        FROM Paciente p
        INNER JOIN HistoriaClinica hc ON p.id_paciente = hc.id_paciente
        INNER JOIN EvaluacionClinica ec ON hc.id_historia_clinica = ec.id_historia_clinica
        ORDER BY p.nombres, p.apellidos
        """
        patients_with_exams = db_manager.execute_query(patients_query)
        
        return render_template('exams.html',
                             evaluations=evaluations,
                             patients_with_exams=patients_with_exams,
                             search=search,
                             selected_patient_id=patient_id)
    
    except Exception as e:
        logger.error(f"Exams page error: {e}")
        flash(f'Error loading exams: {str(e)}', 'error')
        return render_template('exams.html', 
                             evaluations=[], 
                             patients_with_exams=[], 
                             search='', 
                             selected_patient_id='')

# Dashboard routes for different roles
@app.route('/dashboard/enfermera')
def dashboard_nurse():
    """Nurse dashboard with patient care focus"""
    try:
        # Get nurse-specific statistics
        stats = {}
        
        # Total patients under care
        total_patients_query = "SELECT COUNT(*) as count FROM Paciente"
        result = db_manager.execute_single_query(total_patients_query)
        stats['total_patients'] = result['count'] if result else 0
        
        # Recent admissions for nursing notes
        recent_admissions_query = """
        SELECT ap.id_admision, ap.fecha_admision, ap.motivo_ingreso, ap.via_ingreso, ap.observaciones,
               p.nombres, p.apellidos, p.documento_identidad, p.edad, p.sexo
        FROM AdmisionPaciente ap
        LEFT JOIN Paciente p ON ap.id_paciente = p.id_paciente
        ORDER BY ap.fecha_admision DESC
        LIMIT 15
        """
        recent_admissions = db_manager.execute_query(recent_admissions_query)
        
        # Patients needing attention (based on observations)
        attention_needed_query = """
        SELECT ap.id_admision, ap.observaciones, ap.fecha_admision,
               p.nombres, p.apellidos, p.documento_identidad, p.edad
        FROM AdmisionPaciente ap
        LEFT JOIN Paciente p ON ap.id_paciente = p.id_paciente
        WHERE ap.observaciones IS NOT NULL AND ap.observaciones != ''
        ORDER BY ap.fecha_admision DESC
        LIMIT 10
        """
        attention_needed = db_manager.execute_query(attention_needed_query)
        
        return render_template('dashboard_nurse.html', 
                             stats=stats, 
                             recent_admissions=recent_admissions,
                             attention_needed=attention_needed)
    
    except Exception as e:
        logger.error(f"Nurse dashboard error: {e}")
        flash(f'Error loading nurse dashboard: {str(e)}', 'error')
        return render_template('dashboard_nurse.html', stats={}, recent_admissions=[], attention_needed=[])

@app.route('/dashboard/paciente')
def dashboard_patient():
    """Patient dashboard - simplified view"""
    try:
        # For demo purposes, show first patient's data
        # In real implementation, this would be based on logged-in patient
        patient_query = "SELECT * FROM Paciente LIMIT 1"
        patient = db_manager.execute_single_query(patient_query)
        
        if patient:
            # Get patient's clinical histories
            histories_query = """
            SELECT hc.*, ap.fecha_admision, ap.motivo_ingreso,
                   inst.nombre as institucion_nombre
            FROM HistoriaClinica hc
            LEFT JOIN AdmisionPaciente ap ON hc.id_admision = ap.id_admision
            LEFT JOIN InstitucionSalud inst ON hc.id_institucion = inst.id_institucion
            WHERE hc.id_paciente = %s
            ORDER BY ap.fecha_admision DESC
            LIMIT 5
            """
            histories = db_manager.execute_query(histories_query, (patient['id_paciente'],))
            
            # Get recent evaluations
            evaluations_query = """
            SELECT ec.fecha_resultado, ec.instrumento_utilizado, 
                   ec.resultado_parametro, ec.resultado_valor
            FROM EvaluacionClinica ec
            INNER JOIN HistoriaClinica hc ON ec.id_historia_clinica = hc.id_historia_clinica
            WHERE hc.id_paciente = %s
            ORDER BY ec.fecha_resultado DESC
            LIMIT 5
            """
            evaluations = db_manager.execute_query(evaluations_query, (patient['id_paciente'],))
            
        else:
            histories = []
            evaluations = []
            
        return render_template('dashboard_patient.html',
                             patient=patient,
                             histories=histories,
                             evaluations=evaluations)
    
    except Exception as e:
        logger.error(f"Patient dashboard error: {e}")
        flash(f'Error loading patient dashboard: {str(e)}', 'error')
        return render_template('dashboard_patient.html', patient=None, histories=[], evaluations=[])

@app.route('/dashboard/admin')
def dashboard_admin():
    """Admin dashboard with system overview"""
    try:
        # System statistics
        stats = {}
        
        # Database table counts
        tables = ['Paciente', 'HistoriaClinica', 'AdmisionPaciente', 'ProfesionalSalud', 
                 'EvaluacionClinica', 'Diagnostico', 'Tratamiento', 'InstitucionSalud']
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = db_manager.execute_single_query(query)
            stats[table.lower()] = result['count'] if result else 0
        
        # Recent system activity
        activity_query = """
        SELECT 'Admisión' as tipo, ap.fecha_admision as fecha, 
               CONCAT(p.nombres, ' ', p.apellidos) as descripcion
        FROM AdmisionPaciente ap
        LEFT JOIN Paciente p ON ap.id_paciente = p.id_paciente
        WHERE ap.fecha_admision IS NOT NULL
        UNION ALL
        SELECT 'Evaluación' as tipo, ec.fecha_resultado as fecha,
               CONCAT('Evaluación - ', ec.instrumento_utilizado) as descripcion
        FROM EvaluacionClinica ec
        WHERE ec.fecha_resultado IS NOT NULL
        ORDER BY fecha DESC
        LIMIT 20
        """
        recent_activity = db_manager.execute_query(activity_query)
        
        return render_template('dashboard_admin.html',
                             stats=stats,
                             recent_activity=recent_activity)
    
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash(f'Error loading admin dashboard: {str(e)}', 'error')
        return render_template('dashboard_admin.html', stats={}, recent_activity=[])

@app.route('/clinical_histories')
def clinical_histories():
    """Clinical histories list page"""
    try:
        recent_only = request.args.get('recent') == 'true'
        search = request.args.get('search', '')
        
        base_query = """
        SELECT hc.id_historia_clinica, hc.fecha_egreso,
               p.nombres, p.apellidos, p.documento_identidad, p.edad, p.sexo,
               ap.fecha_admision, ap.motivo_ingreso, ap.via_ingreso,
               inst.nombre as institucion_nombre,
               pi.nombres as prof_nombres, pi.apellidos as prof_apellidos
        FROM HistoriaClinica hc
        LEFT JOIN Paciente p ON hc.id_paciente = p.id_paciente
        LEFT JOIN AdmisionPaciente ap ON hc.id_admision = ap.id_admision
        LEFT JOIN InstitucionSalud inst ON hc.id_institucion = inst.id_institucion
        LEFT JOIN ProfesionalSalud pi ON hc.id_profesional_ingreso = pi.id_profesional
        """
        
        conditions = []
        params = []
        
        if search:
            conditions.append("""
            (p.nombres LIKE %s OR p.apellidos LIKE %s OR p.documento_identidad LIKE %s
             OR ap.motivo_ingreso LIKE %s)
            """)
            search_term = f'%{search}%'
            params.extend([search_term] * 4)
        
        if recent_only:
            conditions.append("ap.fecha_admision >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        
        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            query = base_query
            
        query += " ORDER BY ap.fecha_admision DESC LIMIT 50"
        
        histories = db_manager.execute_query(query, params)
        
        return render_template('clinical_histories_list.html',
                             histories=histories,
                             search=search,
                             recent_only=recent_only)
    
    except Exception as e:
        logger.error(f"Clinical histories error: {e}")
        flash(f'Error loading clinical histories: {str(e)}', 'error')
        return render_template('clinical_histories_list.html', histories=[], search='', recent_only=False)

@app.route('/clinical_history/<int:patient_id>/edit', methods=['GET', 'POST'])
def edit_clinical_history(patient_id):
    """Edit clinical history - for doctors to add notes"""
    try:
        if request.method == 'POST':
            # Handle form submission to add new notes
            historia_id = request.form.get('historia_id')
            new_observation = request.form.get('observacion')
            
            if historia_id and new_observation:
                # Update the admission with new observation using a safer approach
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # First get current observations
                        select_query = """
                        SELECT observaciones FROM AdmisionPaciente 
                        WHERE id_admision = (
                            SELECT id_admision FROM HistoriaClinica WHERE id_historia_clinica = %s
                        )
                        """
                        cursor.execute(select_query, (historia_id,))
                        result = cursor.fetchone()
                        
                        # Prepare new observation text
                        current_obs = result['observaciones'] if result and result['observaciones'] else ''
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        new_obs = f"{current_obs}\n[{timestamp}] MÉDICO: {new_observation}" if current_obs else f"[{timestamp}] MÉDICO: {new_observation}"
                        
                        # Update with new observations
                        update_query = """
                        UPDATE AdmisionPaciente SET observaciones = %s 
                        WHERE id_admision = (
                            SELECT id_admision FROM HistoriaClinica WHERE id_historia_clinica = %s
                        )
                        """
                        cursor.execute(update_query, (new_obs, historia_id))
                        conn.commit()
                        
                flash('Nota médica agregada exitosamente', 'success')
                return redirect(url_for('clinical_history', patient_id=patient_id))
        
        # Get patient and clinical history data (same as view)
        return clinical_history(patient_id)
    
    except Exception as e:
        logger.error(f"Edit clinical history error: {e}")
        flash(f'Error editing clinical history: {str(e)}', 'error')
        return redirect(url_for('clinical_history', patient_id=patient_id))

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('base.html'), 500
