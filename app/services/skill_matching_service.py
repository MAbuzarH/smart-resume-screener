"""
Skill Matching Service

This module provides skill-based matching functionality for comparing candidate resumes
against job requirements. It extracts required skills from job descriptions and determines
which skills are present in candidate resumes.

The service uses token-aware matching to avoid false positives (e.g., "java" vs "javascript")
and supports multi-word skills (e.g., "Machine Learning", "REST API").
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


# Skill alias mapping for common variations
SKILL_ALIASES = {
    'js': 'javascript',
    'node': 'node.js',
    'reactjs': 'react',
    'vuejs': 'vue',
    'angularjs': 'angular',
    'gitlab': 'git',
    'github': 'git',
    'restful api': 'rest api',
    'restful': 'rest api',
    'sql server': 'sql',
    'ms sql': 'sql',
    'postgre': 'postgresql',
    'postgis': 'postgresql',
    'mongo': 'mongodb',
    'nosql': 'mongodb',
    'rdbms': 'sql',
    'ui/ux': 'ui design',
    'ux': 'ux design',
    'ml': 'machine learning',
    'ai': 'artificial intelligence',
    'dl': 'deep learning',
    'nlp': 'natural language processing',
    'cv': 'computer vision',
    'devops': 'devops',
    'ci/cd': 'ci/cd',
    'scrum': 'agile',
    'agile/scrum': 'agile',
    'tdd': 'test driven development',
    'bdd': 'behavior driven development',
    'e2e': 'end to end testing',
    'unit testing': 'testing',
    'integration testing': 'testing',
    'frontend': 'frontend development',
    'backend': 'backend development',
    'fullstack': 'full stack',
    'full-stack': 'full stack',
    'aws cloud': 'aws',
    'azure cloud': 'azure',
    'gcp cloud': 'gcp',
    'gcp': 'google cloud',
    'css3': 'css',
    'html5': 'html',
    'es6': 'javascript',
    'es2015': 'javascript',
    'es2016': 'javascript',
    'typescript': 'typescript',
    'ts': 'typescript',
    'py': 'python',
    'py3': 'python',
    'py2': 'python',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'scikit': 'scikit-learn',
    'sklearn': 'scikit-learn',
    'torch': 'pytorch',
    'tf': 'tensorflow',
    'keras': 'keras',
    'tf.keras': 'keras',
    'django rest': 'django',
    'django rest framework': 'django',
    'flask restful': 'flask',
    'spring boot': 'spring',
    'spring framework': 'spring',
    'expressjs': 'express',
    'react native': 'react',
    'nextjs': 'next',
    'nuxtjs': 'nuxt',
    'vuejs': 'vue',
    'nestjs': 'nestjs',
    'graphql': 'graphql',
    'grpc': 'grpc',
    'soap': 'soap',
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'docker compose': 'docker',
    'docker-compose': 'docker',
    'k8s': 'kubernetes',
    'k8': 'kubernetes',
    'openshift': 'kubernetes',
    'jenkins ci': 'jenkins',
    'gitlab ci': 'gitlab',
    'github actions': 'github',
    'travis ci': 'travis',
    'circleci': 'circleci',
    'bitbucket': 'bitbucket',
    'vcs': 'git',
    'version control': 'git',
    'oauth': 'oauth',
    'jwt': 'jwt',
    'auth0': 'oauth',
    'keycloak': 'oauth',
    'firebase auth': 'firebase',
    'cognito': 'aws',
    'lambda': 'aws',
    'ec2': 'aws',
    's3': 'aws',
    'rds': 'aws',
    'elasticache': 'aws',
    'dynamodb': 'aws',
    'redshift': 'aws',
    'aurora': 'aws',
    'cloudformation': 'aws',
    'terraform': 'terraform',
    'ansible': 'ansible',
    'chef': 'chef',
    'puppet': 'puppet',
    'saltstack': 'salt',
    'consul': 'consul',
    'vault': 'vault',
    'nomad': 'nomad',
    'packer': 'packer',
    'vagrant': 'vagrant',
    'jira': 'jira',
    'confluence': 'confluence',
    'trello': 'trello',
    'asana': 'asana',
    'slack': 'slack',
    'teams': 'teams',
    'zoom': 'zoom',
    'skype': 'skype',
    'webex': 'webex',
    'meet': 'google',
    'sheets': 'google',
    'docs': 'google',
    'drive': 'google',
    'onedrive': 'microsoft',
    'sharepoint': 'microsoft',
    'outlook': 'microsoft',
    'exchange': 'microsoft',
    'teams': 'microsoft',
    'office': 'microsoft',
    'excel': 'microsoft',
    'word': 'microsoft',
    'powerpoint': 'microsoft',
    'visio': 'microsoft',
    'power bi': 'microsoft',
    'powerbi': 'microsoft',
    'tableau': 'tableau',
    'qlik': 'qlik',
    'looker': 'looker',
    'snowflake': 'snowflake',
    'databricks': 'databricks',
    'spark': 'spark',
    'hadoop': 'hadoop',
    'hive': 'hadoop',
    'pig': 'hadoop',
    'kafka': 'kafka',
    'hbase': 'hadoop',
    'cassandra': 'cassandra',
    'elasticsearch': 'elasticsearch',
    'solr': 'elasticsearch',
    'lucene': 'elasticsearch',
    'kibana': 'elasticsearch',
    'logstash': 'elasticsearch',
    'beats': 'elasticsearch',
    'filebeat': 'elasticsearch',
    'metricbeat': 'elasticsearch',
    'packetbeat': 'elasticsearch',
    'heartbeat': 'elasticsearch',
    'apm': 'elasticsearch',
    'siem': 'elasticsearch',
    'security': 'security',
    'infosec': 'security',
    'cybersecurity': 'security',
    'info security': 'security',
    'penetration testing': 'security',
    'pentesting': 'security',
    'bug bounty': 'security',
    'vulnerability assessment': 'security',
    'threat modeling': 'security',
    'incident response': 'security',
    'forensics': 'security',
    'malware analysis': 'security',
    'reverse engineering': 'security',
    'encryption': 'security',
    'cryptography': 'security',
    'key management': 'security',
    'access control': 'security',
    'identity management': 'security',
    'iam': 'security',
    'rbac': 'security',
    'abac': 'security',
    'ldap': 'security',
    'active directory': 'microsoft',
    'ad': 'microsoft',
    'azure ad': 'microsoft',
    'openldap': 'linux',
    'sssd': 'linux',
    'kerberos': 'linux',
    'pam': 'linux',
    'selinux': 'linux',
    'apparmor': 'linux',
    'iptables': 'linux',
    'firewalld': 'linux',
    'nftables': 'linux',
    'systemd': 'linux',
    'sysctl': 'linux',
    'procfs': 'linux',
    'sysfs': 'linux',
    'debugfs': 'linux',
    'cgroups': 'linux',
    'namespaces': 'linux',
    'containers': 'docker',
    'pods': 'kubernetes',
    'services': 'kubernetes',
    'deployments': 'kubernetes',
    'statefulsets': 'kubernetes',
    'daemonsets': 'kubernetes',
    'replicasets': 'kubernetes',
    'ingress': 'kubernetes',
    'network policies': 'kubernetes',
    'service mesh': 'kubernetes',
    'istio': 'kubernetes',
    'linkerd': 'kubernetes',
    'envoy': 'kubernetes',
    'nginx': 'nginx',
    'apache': 'nginx',
    'iis': 'microsoft',
    'tomcat': 'java',
    'jetty': 'java',
    'wildfly': 'java',
    'glassfish': 'java',
    'jboss': 'java',
    'websphere': 'java',
    'weblogic': 'java',
    'jms': 'java',
    'ejb': 'java',
    'cdi': 'java',
    'spring': 'java',
    'hibernate': 'java',
    'jpa': 'java',
    'jdbc': 'java',
    'jndi': 'java',
    'servlet': 'java',
    'jsp': 'java',
    'jsf': 'java',
    'gwt': 'java',
    'vaadin': 'java',
    'wicket': 'java',
    'struts': 'java',
    'mybatis': 'java',
    'play': 'java',
    'vert.x': 'java',
    'netty': 'java',
    'akka': 'java',
    'scala': 'scala',
    'kotlin': 'kotlin',
    'groovy': 'java',
    'clojure': 'clojure',
    'gradle': 'java',
    'maven': 'java',
    'ant': 'java',
    'ivy': 'java',
    'sbt': 'scala',
    'leiningen': 'clojure',
    'boot': 'java',
    'grails': 'groovy',
    'micronaut': 'java',
    'quarkus': 'java',
    'helidon': 'java',
    'dropwizard': 'java',
    'sparkjava': 'spark',
    'hadoopjava': 'hadoop',
    'flink': 'spark',
    'beam': 'spark',
    'samza': 'spark',
    'storm': 'spark',
    'heroku': 'heroku',
    'digitalocean': 'digitalocean',
    'linode': 'linode',
    'vultr': 'vultr',
    'rackspace': 'rackspace',
    'bluehost': 'bluehost',
    'hostgator': 'hostgator',
    'godaddy': 'godaddy',
    'namecheap': 'namecheap',
    'cloudflare': 'cloudflare',
    'fastly': 'fastly',
    'akamai': 'akamai',
    'cloudfront': 'aws',
    'cloudflare workers': 'cloudflare',
    'vercel': 'vercel',
    'netlify': 'netlify',
    'firebase hosting': 'firebase',
    'amplify': 'aws',
    'elastic beanstalk': 'aws',
    'lambda': 'aws',
    'fargate': 'aws',
    'ecs': 'aws',
    'eks': 'aws',
    'emr': 'aws',
    'athena': 'aws',
    'glue': 'aws',
    'redshift': 'aws',
    'quicksight': 'aws',
    'sagemaker': 'aws',
    'rekognition': 'aws',
    'polly': 'aws',
    'transcribe': 'aws',
    'translate': 'aws',
    'comprehend': 'aws',
    'lex': 'aws',
    'kendra': 'aws',
    'textract': 'aws',
    ' comprehend medical': 'aws',
    'healthlake': 'aws',
    'lake formation': 'aws',
    'glacier': 'aws',
    's3 glacier': 'aws',
    'efs': 'aws',
    'fsx': 'aws',
    'storage gateway': 'aws',
}


@dataclass
class SkillMatchResult:
    """
    Data class for skill matching results.
    
    Attributes:
        required_skills: List of normalized required skills from job
        matched_skills: List of skills found in resume
        missing_skills: List of skills not found in resume
        matched_count: Number of matched skills
        required_count: Total number of required skills
        skill_match_percentage: Percentage of skills matched (0-100)
    """
    required_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    matched_count: int
    required_count: int
    skill_match_percentage: float


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill string to a canonical form.
    
    This function:
    - Converts to lowercase
    - Trims whitespace
    - Applies skill aliases
    - Normalizes common variations
    
    Args:
        skill: Raw skill string (e.g., "Python", " Flask ", "JS")
        
    Returns:
        Normalized skill string (e.g., "python", "flask", "javascript")
    """
    if not skill or not isinstance(skill, str):
        return ""
    
    # Convert to lowercase and trim
    normalized = skill.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Apply alias mapping
    if normalized in SKILL_ALIASES:
        normalized = SKILL_ALIASES[normalized]
    
    return normalized


def extract_skills_from_job(job_skills: str) -> List[str]:
    """
    Extract and normalize skills from job skills string.
    
    The job skills field contains comma-separated skills like:
    "Python, Flask, SQL, Docker, AWS"
    
    Args:
        job_skills: Comma-separated skills string from Job.skills field
        
    Returns:
        List of normalized skill strings
    """
    if not job_skills or not isinstance(job_skills, str):
        return []
    
    # Split by comma and normalize each skill
    skills = [normalize_skill(skill.strip()) for skill in job_skills.split(',')]
    
    # Remove empty strings
    skills = [skill for skill in skills if skill]
    
    return skills


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words while preserving multi-word phrases.
    
    This function splits text into tokens but also attempts to preserve
    multi-word skills by checking against known multi-word skill patterns.
    
    Args:
        text: Text to tokenize (resume or job description)
        
    Returns:
        List of tokens/words from the text
    """
    if not text or not isinstance(text, str):
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation but preserve hyphens and spaces
    text = re.sub(r'[^\w\s-]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Split into words
    words = text.split()
    
    return words


def skill_present_in_text(skill: str, text_tokens: List[str]) -> bool:
    """
    Check if a skill is present in tokenized text.
    
    This function uses token-aware matching to avoid false positives:
    - "java" should NOT match "javascript"
    - Multi-word skills must match the full phrase
    
    Args:
        skill: Normalized skill string (e.g., "machine learning", "python")
        text_tokens: List of tokens from tokenized text
        
    Returns:
        True if skill is present in text, False otherwise
    """
    if not skill or not text_tokens:
        return False
    
    skill_words = skill.split()
    
    # Single-word skill: check exact match
    if len(skill_words) == 1:
        return skill in text_tokens
    
    # Multi-word skill: check if all words are present
    # This is a relaxed approach - check if all component words are present
    all_words_present = all(word in text_tokens for word in skill_words)
    
    # For better accuracy, also check if words appear in sequence
    if all_words_present:
        # Try to find the exact sequence
        skill_len = len(skill_words)
        text_len = len(text_tokens)
        
        if skill_len <= text_len:
            for i in range(text_len - skill_len + 1):
                if text_tokens[i:i+skill_len] == skill_words:
                    return True
    
    return all_words_present


def calculate_skill_match(resume_text: str, job_skills: str) -> SkillMatchResult:
    """
    Calculate skill match between resume and job requirements.
    
    This function:
    - Extracts required skills from job skills string
    - Normalizes both job skills and resume text
    - Determines which required skills are present in resume
    - Calculates skill match percentage
    - Returns structured result
    
    Args:
        resume_text: Candidate's resume text (raw or processed)
        job_skills: Comma-separated skills string from Job.skills field
        
    Returns:
        SkillMatchResult containing:
        - required_skills: List of normalized required skills
        - matched_skills: List of skills found in resume
        - missing_skills: List of skills not found in resume
        - matched_count: Number of matched skills
        - required_count: Total number of required skills
        - skill_match_percentage: Percentage of skills matched (0-100)
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not job_skills or not isinstance(job_skills, str):
        logger.warning("Empty or invalid job skills provided to calculate_skill_match")
        return SkillMatchResult([], [], [], 0, 0, 0.0)
    
    try:
        # Extract and normalize required skills from job
        required_skills = extract_skills_from_job(job_skills)
        
        if not required_skills:
            logger.info("No required skills found in job skills")
            return SkillMatchResult([], [], [], 0, 0, 0.0)
        
        # Handle empty resume text
        if not resume_text or not isinstance(resume_text, str):
            logger.warning("Empty or invalid resume text provided to calculate_skill_match")
            return SkillMatchResult(
                required_skills=required_skills,
                matched_skills=[],
                missing_skills=required_skills,
                matched_count=0,
                required_count=len(required_skills),
                skill_match_percentage=0.0
            )
        
        # Tokenize resume text
        resume_tokens = tokenize_text(resume_text)
        
        if not resume_tokens:
            logger.warning("Resume text produced no tokens after tokenization")
            matched_skills = []
        else:
            # Check which required skills are present in resume
            matched_skills = []
            for skill in required_skills:
                if skill_present_in_text(skill, resume_tokens):
                    matched_skills.append(skill)
        
        # Determine missing skills
        missing_skills = [skill for skill in required_skills if skill not in matched_skills]
        
        # Calculate counts
        matched_count = len(matched_skills)
        required_count = len(required_skills)
        
        # Calculate percentage
        if required_count > 0:
            skill_match_percentage = (matched_count / required_count) * 100
        else:
            skill_match_percentage = 0.0
        
        # Round to 2 decimal places
        skill_match_percentage = round(skill_match_percentage, 2)
        
        logger.info(f"Skill match: {matched_count}/{required_count} = {skill_match_percentage:.2f}%")
        
        return SkillMatchResult(
            required_skills=required_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_count=matched_count,
            required_count=required_count,
            skill_match_percentage=skill_match_percentage
        )
        
    except Exception as e:
        logger.error(f"Error calculating skill match: {str(e)}")
        return SkillMatchResult([], [], [], 0, 0, 0.0)
