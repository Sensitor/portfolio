public class VoieDuCombat extends Voie {
    public VoieDuCombat() {
        super("Voie du combat");
        competences.add(new Competence("Vivacite", 1));
        competences.add(new Competence("Desarmer", 2));
        competences.add(new Competence("Double attaque", 3));
        competences.add(new Competence("Attaque circulaire", 4));
    }
}
